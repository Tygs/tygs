from unittest.mock import Mock, MagicMock

import pytest
import aiohttp
from aiohttp.web_reqrep import Response

from tygs.http import server
from tygs.exceptions import (
    HttpRequestControllerError, HttpResponseControllerError, RoutingError)


def test_httprequest_controller(app):
    aiohttp_request = Mock()
    httprequest = server.HttpRequestController(app, aiohttp_request)
    mapping = {'server_name': 'host',
               'url_scheme': 'scheme',
               'method': 'method',
               'url_path': 'path',
               'url_query': 'GET'}

    for tygs_name, aio_name in mapping.items():
        assert getattr(httprequest, tygs_name) == getattr(aiohttp_request,
                                                          aio_name)
    assert isinstance(httprequest.response, server.HttpResponseController)
    assert httprequest.url_args == {}
    assert repr(httprequest).startswith('<HttpRequestController')


def test_httpresponse_controller_init(app):
    request = MagicMock()
    request.app = app
    httpresponse = server.HttpResponseController(request)
    assert httpresponse.template_engine is None
    assert httpresponse.status_code == 200
    assert httpresponse.reason == 'OK'
    assert httpresponse.content_type == 'text/html'
    assert httpresponse.charset == 'utf-8'
    assert httpresponse.headers == {}
    with pytest.raises(HttpResponseControllerError):
        httpresponse.render_response()


def test_httpresponse_controller_template(webapp):
    request = MagicMock()
    request.app = webapp
    httpresponse = server.HttpResponseController(request)
    assert httpresponse.template_engine == webapp.components['templates']

    httpresponse.template('template_name', {'foo': 'bar'})

    assert httpresponse.context['template_name'] == 'template_name'
    context = httpresponse._renderer_data.pop('context')
    assert "res" in context and "req" in context
    assert httpresponse._renderer_data == {'foo': 'bar'}

    httpresponse.template('template_name2', {'foo2': 'bar2'})
    context = httpresponse._renderer_data.pop('context')
    assert "res" in context and "req" in context
    assert httpresponse.context['template_name'] == 'template_name2'
    assert httpresponse._renderer_data == {'foo2': 'bar2'}


def test_httpresponse_controller_render_response(webapp):
    request = MagicMock()
    request.app = webapp
    httpresponse = server.HttpResponseController(request)
    httpresponse._renderer = Mock()

    httpresponse.render_response()
    httpresponse._renderer.assert_called_once_with(httpresponse)


def test_httpresponse_build_aiohttp_reponse(webapp):
    request = MagicMock()
    request.app = webapp
    httpresponse = server.HttpResponseController(request)
    httpresponse.render_response = Mock(return_value={
        "body": b"toto",
        "content_type": "text/html",
        "status": 418
    })

    aiohttpres = httpresponse._build_aiohttp_response()

    assert isinstance(aiohttpres, Response)
    assert aiohttpres.body == b"toto"
    assert aiohttpres.content_type == "text/html"
    assert aiohttpres.status == 418


@pytest.mark.asyncio
async def test_404(webapp):
    try:
        await webapp.async_ready()

        with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8080/') as resp:
                assert resp.status == 404
    finally:
        await webapp.async_stop()


@pytest.mark.asyncio
async def test_request_params(queued_webapp):

    app = queued_webapp()
    http = app.components['http']

    @http.get('/')
    def index_controller(req, res):
        return res.text('test')

    await app.async_ready()

    response = await app.client.get('/', params={'param': 'value'})
    request = response.request

    assert 'param' in request
    assert request['param'] == 'value'
    with pytest.raises(HttpRequestControllerError):
        request.GET

    await app.async_stop()


@pytest.mark.asyncio
async def test_request_body(queued_webapp):

    app = queued_webapp()
    http = app.components['http']

    @http.post('/')
    def index_controller(req, res):
        return res.text('')

    await app.async_ready()
    response = await app.client.post('/', params={'param': 'value'})

    request = response.request

    assert 'param' in request
    assert 'fromage' not in request

    await app.async_stop()


@pytest.mark.asyncio
async def test_request_cookies(queued_webapp):

    app = queued_webapp(cookies={'flavour': 'chocolate'})
    http = app.components['http']

    @http.get('/')
    def index_controller(req, res):
        return res.text('')

    try:
        await app.async_ready()
        response = await app.client.get('/')

        request = response.request

        assert 'flavour' in request
        assert 'flavour' in request.cookies
        assert request['flavour'] == 'chocolate'
        assert request.cookies['flavour'] == 'chocolate'

    finally:
        await app.async_stop()


@pytest.mark.asyncio
async def test_request_headers(queued_webapp):

    app = queued_webapp()
    http = app.components['http']

    @http.post('/')
    def index_controller(req, res):
        return res.text('')

    await app.async_ready()
    response = await app.client.post('/', headers={'foo': 'bar'})

    assert response.request.headers['foo'] == 'bar'
    assert response.request.headers['content-length'] == '0'
    await app.async_stop()


@pytest.mark.asyncio
async def test_error_handler(queued_webapp):
    try:
        app = queued_webapp()
        beacon = Mock()
        http = app.components['http']

        @http.on_error('404')
        async def handler_404(req, res):
            await req.load_body()
            assert req['payload'] == 'reblochon'
            beacon()
            return res.text('error')

        await app.async_ready()
        await app.client.post('/fromage', data={'payload': 'reblochon'})
        assert beacon.call_count == 1

    finally:
        await app.async_stop()


@pytest.mark.asyncio
async def test_error_handler_no_load_body(queued_webapp):
    try:
        app = queued_webapp()
        beacon = Mock()
        http = app.components['http']

        @http.on_error('404')
        async def handler_404(req, res):
            with pytest.raises(HttpRequestControllerError):
                assert req['payload'] == 'reblochon'
            beacon()
            return res.text('error')

        await app.async_ready()
        await app.client.post('/fromage', data={'payload': 'reblochon'})
        assert beacon.call_count == 1

    finally:
        await app.async_stop()


@pytest.mark.asyncio
async def test_lazy_loading_controller(queued_webapp):
    try:
        app = queued_webapp()
        beacon = Mock()
        http = app.components['http']

        @http.post('/', lazy_body=True)
        async def handler_404(req, res):
            beacon()
            with pytest.raises(HttpRequestControllerError):
                req['payload']
            return res.text('error')

        await app.async_ready()
        await app.client.post('/', data={'payload': 'test'})
        assert beacon.call_count == 1

    finally:
        await app.async_stop()


@pytest.mark.asyncio
async def test_error_handler_with_lazy(queued_webapp):
    try:
        app = queued_webapp()
        beacon = Mock()
        http = app.components['http']

        @http.on_error('404', lazy_body=True)
        async def handler_404(req, res):
            beacon()
            with pytest.raises(HttpRequestControllerError):
                req['payload']
            return res.text('error')

        await app.async_ready()
        await app.client.post('/fromage', data={'payload': 'reblochon'})
        assert beacon.call_count == 1

    finally:
        await app.async_stop()


@pytest.mark.asyncio
async def test_request_browse(queued_webapp):
    try:
        app = queued_webapp(cookies={'flavour': 'chocolate'})
        beacon = Mock()
        http = app.components['http']

        # @http.route('/', methods=['GET', 'POST'])
        @http.post('/')
        async def handler(req, res):
            with pytest.raises(HttpRequestControllerError):
                req['nope']
            params = {}

            # calling lower() on keys because CIMultiDict's implementation of
            # case insensitive keys call .title() on all the keys
            for key, value in req.items():
                params[key.lower()] = value
            assert params == {'param': 'ok', 'data': 'yup',
                              'flavour': 'chocolate'}

            keys = [key.lower() for key in req]
            assert keys == ['param', 'data', 'flavour']

            values = []
            for item in req.values():
                values.append(item)
            assert values == ['ok', 'yup', 'chocolate']

            assert 'param' in req
            assert 'flavour' in req

            assert len(req) == 3

            with pytest.raises(HttpRequestControllerError):
                req.POST['flavour']

            with pytest.raises(AttributeError):
                req.bleh

            beacon()
            return res.text('')

        await app.async_ready()
        await app.client.post('/', params={'param': 'ok'},
                              data={'data': 'yup'})
        assert beacon.call_count == 1

    finally:
        await app.async_stop()


@pytest.mark.asyncio
async def test_response_browse(queued_webapp):
    try:
        app = queued_webapp()
        beacon = Mock()
        http = app.components['http']

        # @http.route('/', methods=['GET', 'POST'])
        @http.post('/')
        async def handler(req, res):
            with pytest.raises(HttpResponseControllerError):
                res.status
            with pytest.raises(HttpResponseControllerError):
                res.code
            with pytest.raises(AttributeError):
                res.bleh

            beacon()
            return res.text('')

        await app.async_ready()
        await app.client.post('/', params={'param': 'ok'},
                              data={'data': 'yup'})
        assert beacon.call_count == 1

    finally:
        await app.async_stop()


@pytest.mark.asyncio
async def test_invalid_error_handler(webapp):

    http = webapp.components['http']

    with pytest.raises(RoutingError):
        @http.on_error('200')
        async def not_error_handler(req, res):
            return res.text('Everything is awesome!')  # noqa


@pytest.mark.asyncio
async def test_cookie_response(queued_webapp):
    try:
        app = queued_webapp()
        beacon = Mock()
        http = app.components['http']

        @http.get('/')
        async def handler(req, res):

            res.set_cookie('test', 'val')
            res.set_cookie('test2', 'val2')
            res.del_cookie('test2')

            beacon()
            return res.text('')

        await app.async_ready()
        res = await app.client.get('/')
        assert beacon.call_count == 1
        assert 'test' in res.cookies
        assert res.cookies['test'].value == 'val'
        assert 'max-age' not in res.cookies['test']
        assert 'test2' in res.cookies
        assert 'max-age' in res.cookies['test2']
        assert res.cookies['test2']['max-age'] == 0

    finally:
        await app.async_stop()
