from unittest.mock import Mock, MagicMock

from aiohttp.web_reqrep import Response

from tygs.http import server


def test_httprequest_controller(app):
    aiohttp_request = Mock()
    httprequest = server.HttpRequestController(app, aiohttp_request)
    mapping = {'server_name': 'host',
               'url_scheme': 'scheme',
               'method': 'method',
               'path_info': 'path',
               'query_args': 'query_string'}

    for tygs_name, aio_name in mapping.items():
        assert getattr(httprequest, tygs_name) == getattr(aiohttp_request,
                                                          aio_name)
    assert isinstance(httprequest.response, server.HttpResponseController)
    assert httprequest.url_params == {}
    assert repr(httprequest).startswith('<HttpRequestController')


def test_httpresponse_controller_init(app):
    request = MagicMock()
    request.app = app
    httpresponse = server.HttpResponseController(request)
    assert httpresponse.template_engine is None
    assert httpresponse.status == 200
    assert httpresponse.reason == 'OK'
    assert httpresponse.content_type == 'text/html'
    assert httpresponse.charset == 'utf-8'
    assert httpresponse.headers == {}
    assert httpresponse.data == {}


def test_httpresponse_controller_template(webapp):
    request = MagicMock()
    request.app = webapp
    httpresponse = server.HttpResponseController(request)
    assert httpresponse.template_engine == webapp.components['templates']

    httpresponse.template('template_name', {'foo': 'bar'})

    assert httpresponse.template_name == 'template_name'
    assert httpresponse.data == {'foo': 'bar'}

    httpresponse.template('template_name2', {'foo2': 'bar2'})

    assert httpresponse.template_name == 'template_name2'
    assert httpresponse.data == {'foo': 'bar', 'foo2': 'bar2'}


def test_httpresponse_controller_render_response(webapp):
    request = MagicMock()
    request.app = webapp
    httpresponse = server.HttpResponseController(request)
    httpresponse.renderer = Mock()

    httpresponse.render_response()
    httpresponse.renderer.assert_called_once_with(httpresponse)


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
