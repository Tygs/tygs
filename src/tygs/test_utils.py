from unittest.mock import Mock


class AsyncMock(Mock):

    def __call__(self, *args, **kwargs):
        parent = super(AsyncMock, self)
        async def coro():
            return parent.__call__(*args, **kwargs)
        return coro()

    def __await__(self):
        return self().__await__()
