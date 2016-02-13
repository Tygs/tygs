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
        # than this like project.init, project.ready, app_name.init, app_name.ready,
        # etc.
        # TODO: allow to pass arguments in events.
        # TODO: allow synchronous events
        await self.change_state('init')

        await self.change_state('ready')
        # Not awaiting so all callbacks from here are no blocking.
        return self.change_state('running')

    async def async_ready(self, cwd=None):
        return await self.setup(cwd)

    def ready(self, cwd=None):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_ready())
        try:
            loop.run_forever()
        except RuntimeError as e:
            # TODO: remove typographic quotes as they can not be encoded to ascii
            # Exception messages and __repr__ in Python should always be ascii
            # comptible
            raise RuntimeError('app.ready() can’t be called while an event '
                               'loop is running, maybe you want to call '
                               '“await app.async_ready()” instead?') from e
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    async def async_stop(self):
        return await self.trigger('stop')

    def stop(self):
        # TODO: we are basically using the same code as async_top, but
        # stopping the loop and running it manually. Let's DRY and reuse
        # async_stop
        loop = asyncio.get_event_loop()
        loop.stop()
        loop.run_until_complete(self.async_stop())
        loop.close()


