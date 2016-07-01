

from unittest.mock import Mock

from requests.models import RequestEncodingMixin

from aiohttp.streams import StreamReader


class AsyncMock(Mock):

    async def __call__(self, *args, **kwargs):
        parent = super(AsyncMock, self)
        return parent.__call__(*args, **kwargs)
        # async def coro():
        #     return parent.__call__(*args, **kwargs)
        # return coro()

    def __await__(self):
        return self().__await__()


def aiohttp_payload(data, encoding="utf8"):
    payload = RequestEncodingMixin._encode_params(data).encode(encoding)
    stream = StreamReader()
    stream.feed_data(payload)
    stream.feed_eof()
    return stream
