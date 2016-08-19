import signal
import asyncio
import weakref

from textwrap import dedent

from path import Path

from .components import SignalDispatcher
from .utils import (get_project_dir, ensure_awaitable, DebugException,
                    silence_loop_error_log, aioloop)


class App:

    def __init__(self, ns):
        self.ns = ns
        self.components = {'signals': SignalDispatcher(self)}
        self.project_dir = None
        self.state = "pristine"
        self.main_future = None
        self.loop = asyncio.get_event_loop()
        self.fail_fast_mode = False

    def fail_fast(self, on=False):
        if on:
            task_factory = DebugException.create_task_factory(self)
            self.loop.set_task_factory(task_factory)
            self.fail_fast_mode = True
        else:
            if DebugException.fail_fast_mode:
                self.loop.set_task_factory(DebugException.old_factory)
                DebugException.old_factory = None
                DebugException.fail_fast_mode = False
            self.fail_fast_mode = False

    def on(self, event):
        return self.components['signals'].on(event)

    def register(self, event, handler):
        return self.components['signals'].register(event, handler)

    def trigger(self, event):
        return self.components['signals'].trigger(event)

    def change_state(self, value):
        self.state = value
        return self.trigger(value)

    async def setup_environnement(self, cwd=None):
        """ Set project dir """
        if cwd is None:
            cwd = get_project_dir()
        self.project_dir = Path(cwd)

    async def setup_components(self):
        components = self.components.values()
        futures = [ensure_awaitable(c.setup) for c in components]
        # waiting for answer for BDFL
        return await asyncio.gather(*futures)

    async def setup(self, cwd=None):

        await self.change_state('setup')

        # Set project dir
        await self.setup_environnement(cwd)
        # Tell all components to hook them self to the events they want to
        # react to

        await self.setup_components()

        # TODO: create a namespace for the events. We will want more details
        # like project.init, project.ready, app_name.init, app_name.ready, etc.
        # TODO: allow to pass arguments in events.
        # TODO: allow synchronous events

        await self.change_state('init')

        await self.change_state('ready')

        # Not awaiting so all callbacks from here are not blocking.
        return self.change_state('running')

    async def async_ready(self, cwd=None):
        task = asyncio.ensure_future(self.setup(cwd))

        # Ensure we drain any exception raised during our setup that
        # we didn't handle
        def on_main_future_done(fut):
            fut.exception()

        task.add_done_callback(on_main_future_done)

        self.main_future = weakref.ref(await task)

        return task

    def ready(self, cwd=None, force_new_loop=False):

        if force_new_loop:
            self.loop = aioloop()

        # If we are killed, try to gracefully exit
        if self.loop.is_running():
            raise RuntimeError("app.ready() can't be called while an event"
                               ' loop is running, maybe you want to call '
                               '"await app.async_ready()" instead?')

        if self.loop.is_closed():
            raise RuntimeError(dedent("""
                App.ready() can't be called while the event loop is closed.

                Check that you don't close it by mistake.

                Alternatively, you can install a fresh loop before calling
                App.ready() by either:

                 - passing ready(force_new_loop=True);
                 - calling tygs.utils.aioloop();
                 - use one of the asyncio's *EventLoopPolicy API to create
                   a new loop manually.

            """))

        # TODO: create a new event loop policy to warn other dev about
        # changing the event loop once it's set

        self._add_signal_handlers(('SIGINT', 'SIGTERM'), self.stop)

        clean = False  # do not stop cleanly if the user made a mistake
        try:
            # Main loop, most of the work happens here
            self.main_future = asyncio.ensure_future(self.async_ready(cwd))

            # Ensure we drain any exception raised during our setup that
            # we didn't handle
            def on_main_future_done(fut):
                fut.exception()

            self.main_future.add_done_callback(on_main_future_done)

            clean = True
            self.loop.run_forever()

        except DebugException as e:
            clean = False
            raise e.from_exception from None

        # On Ctrl+C, try a clean stop. Yes, we need it despite
        # add_signal_handler for an unknown reason.
        except KeyboardInterrupt:
            self.stop()

        # stop() is just setting a state and asking the loop to stop.
        # In the finally, we call _finish(), which on clean exit will run
        # callbacks register to the "stop" event force stop the loop and
        # close it.
        finally:
            if clean:
                self._finish()

    async def async_stop(self):
        return await self.change_state('stop')

    def stop(self):
        """
        Stops the loop, which will trigger a clean app stop later.
        """

        self.state = 'stopping'
        if self.loop.is_running():
            # This stops the loop, and activate ready()'s finally which
            # will enventually call self._stop().
            self.loop.stop()

    def break_loop_with_error(self, msg, exception=RuntimeError):
        # Silence other exception handlers, since we want to break
        # everything.
        with silence_loop_error_log(self.loop):
            raise DebugException(exception(msg))

    def _add_signal_handlers(self, names, callback):
        # Since we are handling the loop, we ensure to call stop if we
        # receive a sigint or sigterm
        for signame in names:
            self.loop.add_signal_handler(getattr(signal, signame),
                                         callback)

    def _finish(self):

        if self.state != "stop":
            if self.state != 'stopping':
                # TODO: it would be better to be able to see RuntimeError
                # directly but we can't figure how to do it now
                msg = "Don't call _finish() directly. Call stop()"
                self.break_loop_with_error(msg)
            self.state = 'stop'
            self.loop.run_until_complete(self.async_stop())

            # TODO : should we really close the loop ?
            self.loop.close()
