import asyncio

from path import Path

from .components import SignalDispatcher
from .utils import get_project_dir, ensure_awaitable


class App:

    def __init__(self, ns):
        self.ns = ns
        self.components = {'signals': SignalDispatcher(self)}
        self.project_dir = None
        self.state = "pristine"
        self.main_future = None

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
        self.main_future = self.change_state('running')
        return self.main_future

    async def async_ready(self, cwd=None):
        self.main_future = self.setup(cwd)
        return await asyncio.ensure_future(self.main_future)

    def ready(self, cwd=None):
        loop = asyncio.get_event_loop()
        # loop.run_until_complete(self.async_ready())
        try:
            self.main_future = asyncio.ensure_future(self.async_ready())
            clean = True
            loop.run_forever()
        except RuntimeError as e:
            clean = False  # do not stop cleanly if the user made a mistake
            if loop.is_running():
                raise RuntimeError("app.ready() can't be called while an event"
                                   ' loop is running, maybe you want to call '
                                   '"await app.async_ready()" instead?') from e
            else:
                raise RuntimeError("app.ready() can't be called while an event"
                                   ' closed event loop. Please install a fresh'
                                   ' one with policy.new_event_loop() or make '
                                   "sure you don't close it by mistake") from e
        except KeyboardInterrupt:
            pass
        finally:
            if clean and not self.state == "stop":
                self.stop()

    async def async_stop(self):
        return await self.change_state('stop')

    def stop(self):
        self.state = 'stop'
        loop = asyncio.get_event_loop()
        loop.stop()
        loop.run_until_complete(self.async_stop())
        loop.close()
        exception = self.main_future.exception()
        if not isinstance(exception, KeyboardInterrupt):
            raise exception
