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

    # TODO: rename this method. setup_lifecycle is a poor name. schedule_lifecycle_steps?
    async def setup_lifecycle(self):

        # TODO: find a better name. "prepare" is not really explicit. We use
        # prepare to actually trigger the very first code of components, which
        # in fact is mostly used to attach to init.
        # Somethin like load() or mount() would be more appropriate.

        # TODO: this should be a separate method and be unit tested. something
        # like mount_components(). Also, since it's blocking, it should be
        # called outside of setup_lifecycle and be document as a place were
        # you still can block.
        for component in self.components.values():
            component.prepare()

        # TODO: create a namespace for the events. We will want more details
        # than this like project.init, project.ready, app_name.init, app_name.ready,
        # etc.
        # TODO: allow to pass arguments in events.
        # TODO: allow synchronous events
        await asyncio.gather(*self.trigger('init'))
        await asyncio.gather(*self.trigger('ready'))
        # Not awaiting so all callbacks from here are no blocking.
        return asyncio.gather(*self.trigger('running'))

    def ready(self, cwd=None):
        # TODO: this should be it's own method. Something like setup_environnement()
        if cwd is None:
            cwd = get_project_dir()
        self.project_dir = Path(cwd)

        # TODO: calling ensure_future is redundant, as setup_lifecycle is
        # returns a future_already
        asyncio.ensure_future(self.setup_lifecycle())
        loop = asyncio.get_event_loop()
        # TODO: this should be a separate method. Really ready should just be
        # a series of call:
        # - self.setup_environnement()
        # - self.mount_components()
        # - self.schedule_lifecycle_steps()
        # - self.start_event_loop()
        # This will be easier to understand, and easier to test.
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

    async def async_ready(self, cwd=None):
        if cwd is None:
            cwd = get_project_dir()
        self.project_dir = Path(cwd)
        task = await self.setup_lifecycle()
        return task

    def stop(self):
        # TODO: we are basically using the same code as async_top, but
        # stopping the loop and running it manually. Let's DRY and reuse
        # async_stop
        loop = asyncio.get_event_loop()
        futures = asyncio.gather(*self.trigger('stop'))
        loop.stop()
        loop.run_until_complete(futures)
        loop.close()

    async def async_stop(self):
        # TODO: calling ensure_future is redundant, as gather already returns one
        futures = asyncio.gather(*self.trigger('stop'))
        return asyncio.ensure_future(futures)
