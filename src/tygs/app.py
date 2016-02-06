import asyncio

from path import Path

from .components import SignalDispatcher
from .utils import get_project_dir


class App:

    def __init__(self, ns):
        self.ns = ns
        self.components = {'signals': SignalDispatcher(self)}
        self.project_dir = None

    def on(self, event):
        return self.components['signals'].on(event)

    def register(self, event, handler):
        return self.components['signals'].register(event, handler)

    def trigger(self, event):
        return self.components['signals'].trigger(event)

    async def setup_lifecycle(self):
        for component in self.components.values():
            component.prepare()
        await asyncio.gather(*self.trigger('init'))
        await asyncio.gather(*self.trigger('ready'))
        return asyncio.gather(*self.trigger('running'))

    def ready(self, cwd=None):
        if cwd is None:
            cwd = get_project_dir()
        self.project_dir = Path(cwd)
        task = self.setup_lifecycle()
        loop = asyncio.get_event_loop()
        try:
            loop.run_forever()
        except RuntimeError as e:
            raise RuntimeError('app.ready() can’t be called while an event '
                               'loop is running, maybe you want to call '
                               '“await app.async_ready()” instead?') from e
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
        return task

    def async_ready(self, cwd=None):
        if cwd is None:
            cwd = get_project_dir()
        self.project_dir = Path(cwd)
        task = self.setup_lifecycle()
        return task

    def stop(self):
        loop = asyncio.get_event_loop()
        futures = asyncio.gather(*self.trigger('stop'))
        loop.stop()
        loop.run_until_complete(futures)
        loop.close()

    async def async_stop(self):
        futures = asyncio.gather(*self.trigger('stop'))
        return asyncio.ensure_future(futures)
