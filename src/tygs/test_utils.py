

import asyncio

from unittest.mock import Mock


class AsyncMock(Mock):

    pending_tasks = []

    def __call__(self, *args, **kwargs):
        async def coro():
            super(AsyncMock, self).__call__(*args, **kwargs)
        return coro()

    def __await__(self):
        task = asyncio.ensure_future(self())
        self.pending_tasks.append(task)
        return task
