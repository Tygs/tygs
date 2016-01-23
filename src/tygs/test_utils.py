import asyncio
from unittest.mock import Mock


class AsyncMock(Mock):

    def __call__(self, *args, **kwargs):
        call = super().__call__(*args, **kwargs)
        async def coro(*args, **kwargs):
            return call
        return asyncio.ensure_future(coro())
