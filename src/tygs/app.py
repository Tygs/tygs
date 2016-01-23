import asyncio

from .components import SignalDispatcher
from .utils import get_project_dir


class App:

    def __init__(self, ns):
        self.ns = ns
        self.components = {'signals': SignalDispatcher()}
        self.project_dir = None

    def on(self, event):
        return self.components['signals'].on(event)

    def register(self, event, handler):
        return self.components['signals'].register(event, handler)

    def trigger(self, event):
        return self.components['signals'].trigger(event)

    async def setup_lifecycle(self):
        futures = self.trigger('init')
        await asyncio.gather(*futures)
        self.trigger('ready')

    def ready(self, cwd=None):
        if cwd is None:
            cwd = get_project_dir()
        self.project_dir = cwd
        asyncio.ensure_future(self.setup_lifecycle())
        loop = asyncio.get_event_loop()
        if not loop.is_running():
            try:
                loop.run_forever()
            except KeyboardInterrupt:
                pass
            finally:
                self.stop(True)

    def stop(self, close_loop=False):
        loop = asyncio.get_event_loop()
        async def future():
            futures = self.trigger('stop')
            try:
                await asyncio.gather(*futures)
            finally:
                # TODO: add a logging system
                if close_loop:
                    loop.close()
        asyncio.ensure_future(future())
