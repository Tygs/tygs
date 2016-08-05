from unittest import mock

import pytest

from aiohttp.signals import Signal
from aiohttp.web import Request
from aiohttp.multidict import CIMultiDict
from aiohttp.protocol import HttpVersion
from aiohttp.protocol import RawRequestMessage

# taken from aiohttp tests
# see:https://github.com/KeepSafe/aiohttp/blob/master/tests/test_web_request.py


@pytest.fixture
def aiohttp_request():

    def maker(method, path, headers=None, *,
              version=HttpVersion(1, 1), closing=False,
              sslcontext=None,
              secure_proxy_ssl_header=None):
        if version < HttpVersion(1, 1):  # noqa
            closing = True

        if headers is None:
            headers = {}
        headers = CIMultiDict(headers)

        app = mock.Mock()
        app._debug = False
        app.on_response_prepare = Signal(app)

        if "HOST" not in headers:
            headers["HOST"] = "test.local"  # noqa

        message = RawRequestMessage(method, path, version, headers,
                                    [(k.encode('utf-8'), v.encode('utf-8'))
                                     for k, v in headers.items()],
                                    closing, False)
        payload = mock.Mock()
        transport = mock.Mock()

        def get_extra_info(key):  # noqa
            if key == 'sslcontext':
                return sslcontext
            else:
                return None

        transport.get_extra_info.side_effect = get_extra_info
        writer = mock.Mock()
        reader = mock.Mock()
        req = Request(app, message, payload,
                      transport, reader, writer,
                      secure_proxy_ssl_header=secure_proxy_ssl_header)

        return req
    return maker
