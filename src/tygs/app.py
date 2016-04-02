import signal
import asyncio

from path import Path

from .components import SignalDispatcher
from .utils import get_project_dir, ensure_awaitable, create_task_factory


class App:

    def __init__(self, ns):
        self.ns = ns
        self.components = {'signals': SignalDispatcher(self)}
        self.project_dir = None
        self.state = "pristine"
        self.main_future = None
        loop = asyncio.get_event_loop()
        loop.set_task_factory(create_task_factory(loop))

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
        # Set project dir
        await self.setup_environnement(cwd)
        # Tell all component to hook them self to the events they want to react
        # to
        await self.setup_components()

        # TODO: create a namespace for the events. We will want more details
        # like project.init, project.ready, app_name.init, app_name.ready, etc.
        # TODO: allow to pass arguments in events.
        # TODO: allow synchronous events
        await self.change_state('init')

        await self.change_state('ready')
        # Not awaiting so all callbacks from here are no blocking.
        return self.change_state('running')

    async def async_ready(self, cwd=None):
        self.main_future = await asyncio.ensure_future(self.setup(cwd))
        return self.main_future

    def ready(self, cwd=None):
        loop = asyncio.get_event_loop()
        for signame in ('SIGINT', 'SIGTERM'):
            loop.add_signal_handler(getattr(signal, signame),
                                    self.stop)
        clean = False  # do not stop cleanly if the user made a mistake
        try:
            fut = asyncio.ensure_future(self.async_ready(cwd))
            clean = True
            loop.run_forever()
        except RuntimeError as e:
            if loop.is_running():
                try:
                    fut.cancel()
                except NameError:  # noqa
                    pass
                raise RuntimeError("app.ready() can't be called while an event"
                                   ' loop is running, maybe you want to call '
                                   '"await app.async_ready()" instead?') from e
            else:
                raise RuntimeError("app.ready() can't be called while a "
                                   ' closed event loop. Please install a fresh'
                                   ' one with policy.new_event_loop() or make '
                                   "sure you don't close it by mistake") from e
        finally:
            if clean:
                self._stop()

    async def async_stop(self):
        return await self.change_state('stop')

    def stop(self):
        """
        Stops the loop, which will trigger a clean app stop later.
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            self.state = 'stopping'
            loop.stop()

    def _stop(self, timeout=5):
        if self.state != "stop":
            loop = asyncio.get_event_loop()
            if self.state != 'stopping':
                loop.stop()
            self.state = 'stop'
            loop.run_until_complete(self.async_stop())
            loop.close()
            self.main_future.exception()
