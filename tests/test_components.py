import pytest
from unittest.mock import MagicMock

import jinja2

from tygs import components, app
from tygs.components import AioHttpRequestHandlerAdapter
from tygs.test_utils import AsyncMock
from tygs.http.server import (Router, HttpResponseController,
                              HttpRequestController)
from tygs.app import App

from aiohttp.multidict import CIMultiDict
from aiohttp.protocol import HttpVersion, RawRequestMessage


def test_component():
    c = components.Component('bla')
    assert c.app == 'bla'


@pytest.mark.asyncio
async def test_signal_dispatcher():
    s = components.SignalDispatcher(App('test'))
    assert s.signals == {}

    amock = AsyncMock()
    amock2 = AsyncMock()
    amock3 = AsyncMock()

    handler = amock()
    handler2 = amock2()
    handler3 = amock3()

    s.register('wololo', handler)

    assert len(s.signals) == 1
    assert handler in s.signals['wololo']

    s.register('event', handler2)
    assert len(s.signals) == 2
    assert handler2 in s.signals['event']

    # Using the same name add an handler to the list of handlers for this event
    s.register('wololo', handler3)

    assert len(s.signals) == 2
    assert len(s.signals['wololo']) == 2
    assert handler3 in s.signals['wololo']
    assert handler in s.signals['wololo']

    await s.trigger('wololo')

    amock.assert_called_once_with()
    amock3.assert_called_once_with()
    assert amock2.call_count == 0


def test_signal_dispatcher_decorator():
    s = components.SignalDispatcher(App('test'))
    s.register = MagicMock()

    mock = AsyncMock()
    mock = s.on('event')(mock)

    s.register.assert_called_once_with('event', mock)


@pytest.mark.asyncio
async def test_jinja2_renderer():
    my_app = app.App('test')

    my_app.components['renderer'] = components.Jinja2Renderer(my_app)

    my_app.project_dir = MagicMock()
    await my_app.async_ready()

    assert hasattr(my_app.components['renderer'], 'env')
    assert isinstance(my_app.components['renderer'].env.loader,
                      jinja2.FileSystemLoader)
    assert my_app.components['renderer'].env.autoescape

    await my_app.async_stop()


@pytest.mark.asyncio
async def test_jinja2_renderer_render(app, fixture_dir):

    jinja = components.Jinja2Renderer(app)
    app.components['renderer'] = jinja

    app.project_dir = fixture_dir

    await jinja.lazy_init()

    s = jinja.render_to_string('hello.html', {'foo': 'doh'})
    assert s == "doh: bar"


def test_jinja2_renderer_render_to_response_dict(app):
    req = MagicMock()
    req.app.components.get.return_value = \
        components.Jinja2Renderer(app)

    resp = HttpResponseController(req)
    render = MagicMock()
    render.return_value = 'Hey, I’m a body!'
    resp.template_engine.render_to_string = render
    resp.template_name = 'test_resp.html'

    rendered = resp.template_engine.render_to_response_dict(resp)

    assert isinstance(rendered, dict)
    assert len(rendered) == 6
    assert rendered == {'status': 200, 'reason': 'OK',
                        'content_type': 'text/html',
                        'charset': 'utf-8',
                        'headers': {},
                        'body': 'Hey, I’m a body!'.encode()}
    render.assert_called_once_with('test_resp.html', {})


@pytest.mark.asyncio
async def test_http_component_get(app):

    http = components.HttpComponent(app)
    assert isinstance(http.router, Router)
    http.router.add_route = MagicMock()

    @http.get('/troloo')
    def foo():
        pass

    args = ['/troloo', 'namespace.foo', foo]
    kwargs = {'methods': ['GET']}
    http.router.add_route.assert_called_once_with(*args, **kwargs)


@pytest.mark.asyncio
async def test_http_component_post(app):

    http = components.HttpComponent(app)
    assert isinstance(http.router, Router)
    http.router.add_route = MagicMock()

    @http.post('/troloo')
    def foo():
        pass

    args = ['/troloo', 'namespace.foo', foo]
    kwargs = {'methods': ['POST']}
    http.router.add_route.assert_called_once_with(*args, **kwargs)


@pytest.mark.asyncio
async def test_http_component_put(app):

    http = components.HttpComponent(app)
    assert isinstance(http.router, Router)
    http.router.add_route = MagicMock()

    @http.put('/troloo')
    def foo():
        pass

    args = ['/troloo', 'namespace.foo', foo]
    kwargs = {'methods': ['PUT']}
    http.router.add_route.assert_called_once_with(*args, **kwargs)


@pytest.mark.asyncio
async def test_http_component_patch(app):

    http = components.HttpComponent(app)
    assert isinstance(http.router, Router)
    http.router.add_route = MagicMock()

    @http.patch('/troloo')
    def foo():
        pass

    args = ['/troloo', 'namespace.foo', foo]
    kwargs = {'methods': ['PATCH']}
    http.router.add_route.assert_called_once_with(*args, **kwargs)


@pytest.mark.asyncio
async def test_http_component_options(app):

    http = components.HttpComponent(app)
    assert isinstance(http.router, Router)
    http.router.add_route = MagicMock()

    @http.options('/troloo')
    def foo():
        pass

    args = ['/troloo', 'namespace.foo', foo]
    kwargs = {'methods': ['OPTIONS']}
    http.router.add_route.assert_called_once_with(*args, **kwargs)


@pytest.mark.asyncio
async def test_http_component_head(app):

    http = components.HttpComponent(app)
    assert isinstance(http.router, Router)
    http.router.add_route = MagicMock()

    @http.head('/troloo')
    def foo():
        pass

    args = ['/troloo', 'namespace.foo', foo]
    kwargs = {'methods': ['HEAD']}
    http.router.add_route.assert_called_once_with(*args, **kwargs)


@pytest.mark.asyncio
async def test_http_component_delete(app):

    http = components.HttpComponent(app)
    assert isinstance(http.router, Router)
    http.router.add_route = MagicMock()

    @http.delete('/troloo')
    def foo():
        pass

    args = ['/troloo', 'namespace.foo', foo]
    kwargs = {'methods': ['DELETE']}
    http.router.add_route.assert_called_once_with(*args, **kwargs)


@pytest.fixture
def handleradapter(webapp):
    adapter = AioHttpRequestHandlerAdapter(MagicMock(),
                                           MagicMock(),
                                           webapp.components['http'].router,
                                           tygs_app=webapp)
    adapter.transport = MagicMock()
    return adapter


@pytest.fixture
def aiohttpmsg():
    def factory(method="GET", url="/toto", headers=None):
        headers = CIMultiDict(headers or {})
        if "HOST" not in headers:  # noqa
            headers['HOST'] = "test.local"
        return RawRequestMessage(method, url, HttpVersion(1, 1),
                                 headers, [], False, False)
    return factory


# and I'm not sorry this time
@pytest.mark.asyncio
async def test_requesthandleradapter_tygs_request_from_message(handleradapter,
                                                               aiohttpmsg):

    message = aiohttpmsg('OPTIONS', '/toto')
    request = await handleradapter._tygs_request_from_message(message,
                                                              MagicMock())

    assert isinstance(request, HttpRequestController)
    assert request.method == 'OPTIONS' == handleradapter._meth
    assert request.path_info == '/toto' == handleradapter._path


@pytest.mark.asyncio
async def test_requesthandleradapter_get_handler_and_tygs_req(handleradapter,
                                                              aiohttpmsg):

    message = aiohttpmsg('OPTIONS', '/toto')

    def toto():
        pass  # noqa

    handleradapter._router.add_route('/toto', 'toto_url', toto)

    req, handler = await handleradapter._get_handler_and_tygs_req(message,
                                                                  MagicMock())

    assert isinstance(req, HttpRequestController)
    assert req.method == 'OPTIONS'
    assert req.path_info == '/toto'
    assert handler == toto


@pytest.mark.asyncio
async def test_requesthandleradapter_handle_request(handleradapter,
                                                    aiohttpmsg):

    handleradapter.access_log = True
    handleradapter.log_access = MagicMock()
    handleradapter._write_response_to_client = AsyncMock()

    beacon = MagicMock()

    req_res = []

    async def toto(req, res):
        assert req.path_info == "/toto"
        assert req.method == "GET"
        req_res.extend((req, res))
        beacon()
        return res

    handleradapter._router.add_route('/toto', 'toto_url', toto)

    message = aiohttpmsg('GET', '/toto')
    await handleradapter.handle_request(message, MagicMock())

    handleradapter._write_response_to_client.assert_called_once_with(*req_res)

    beacon.assert_called_once_with()

    assert handleradapter._meth == "none"
    assert handleradapter._path == "none"
    assert handleradapter.log_access.call_count == 1


@pytest.mark.asyncio
async def test_requesthandleradapter_handle_request_without_log(handleradapter,
                                                                aiohttpmsg):

    handleradapter.access_log = False
    handleradapter.log_access = MagicMock()
    handleradapter._write_response_to_client = AsyncMock()

    async def toto(req, res):
        return res

    handleradapter._router.add_route('/toto', 'toto_url', toto)

    message = aiohttpmsg('GET', '/toto')
    await handleradapter.handle_request(message, MagicMock())

    assert handleradapter.log_access.call_count == 0


@pytest.mark.asyncio
async def test_requesthandleradapter_write_response_to_client(handleradapter,
                                                              webapp):

    resp_msg = MagicMock()
    resp_msg.keep_alive = MagicMock(return_value='wololo')

    aiothttp_req = MagicMock()
    aiohttp_res = AsyncMock()
    aiohttp_res.prepare = AsyncMock(return_value=resp_msg)

    req = HttpRequestController(webapp, aiothttp_req)
    res = req.response
    res._build_aiohttp_response = MagicMock(return_value=aiohttp_res)

    handleradapter.keep_alive = MagicMock()

    await handleradapter._write_response_to_client(req, res)

    aiohttp_res.prepare.assert_called_once_with(aiothttp_req)
    aiohttp_res.write_eof.assert_called_once_with()
    handleradapter.keep_alive.assert_called_once_with("wololo")
    resp_msg.keep_alive.assert_called_once_with()
