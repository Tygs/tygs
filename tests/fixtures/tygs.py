import pytest
from functools import partial
import asyncio

from unittest.mock import MagicMock

from path import Path
import aiohttp

from tygs.webapp import WebApp
from tygs.app import App
from tygs.utils import HTTP_VERBS
from tygs.components import (
    AioHttpRequestHandlerAdapter,
    aiohttp_request_handler_factory_adapter_factory
)


@pytest.fixture
def webapp():
    app = WebApp("namespace")
    return app


@pytest.fixture
def client():

    class TestClient():

        def __init__(self, url='http://localhost:8080'):
            self.url = url
            self.q = asyncio.Queue()

            for meth in HTTP_VERBS:
                setattr(self, meth.lower(),
                        partial(self.request, meth.lower()))

        async def request(self, method, url, *args, **kwargs):
            with aiohttp.ClientSession() as session:
                async with getattr(session, method)(self.url + url,
                                                    *args, **kwargs) as resp:

                    await resp.text()
            return await self.q.get()

    test_client = TestClient()
    return test_client


@pytest.fixture
def queued_webapp(client):

    class TestHandlerAdapter(AioHttpRequestHandlerAdapter):

        def _write_response_to_client(self, request, response):
            asyncio.ensure_future(client.q.put(response))
            return super()._write_response_to_client(request, response)

    test_factory_adapter = partial(
        aiohttp_request_handler_factory_adapter_factory,
        handler_adapter=TestHandlerAdapter)

    app = WebApp("namespace", factory_adapter=test_factory_adapter)
    app.client = client
    return app


@pytest.fixture
def app():
    app = App("namespace")
    return app


@pytest.fixture
def fixture_dir():
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def app_with_mocked_signal_dispatcher():

    app = App("namespace")
    signal_mock = MagicMock(app.components['signals'])
    app.components['signals'] = signal_mock
    return app
