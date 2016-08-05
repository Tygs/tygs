
import pytest

from unittest.mock import Mock

from tygs.http.server import Router, HttpRequestController

from werkzeug.routing import Map
from werkzeug.exceptions import NotFound


def test_create_router():
    router = Router()
    assert isinstance(router.url_map, Map)
    assert len(list(router.url_map.iter_rules())) == 0
    assert router.handlers == {}


def test_add_route():
    router = Router()

    def toto():
        pass

    router.add_route('/toto', 'toto_url', toto)

    assert router.handlers['toto_url'] == toto

    rule = next(router.url_map.iter_rules())
    assert rule.endpoint == "toto_url"
    assert rule.rule == '/toto'


@pytest.mark.asyncio
async def test_get_handler(app, aiohttp_request):
    router = Router()

    beacon = Mock()

    def toto():
        beacon()

    router.add_route('/toto', 'toto_url', toto)

    req = aiohttp_request('GET', "/toto")
    tygs_request = HttpRequestController(app, req)
    # get_handler is asyncronous
    coro = router.get_handler(tygs_request)
    handler, arguments = await coro
    handler()
    beacon.assert_called_once_with()


@pytest.mark.asyncio
async def test_get_handler_404(app, aiohttp_request):
    router = Router()

    def toto():
        pass

    router.add_route('/toto', 'toto_url', toto)

    req = aiohttp_request('GET', "/tata")
    tygs_request = HttpRequestController(app, req)
    coro = router.get_handler(tygs_request)

    with pytest.raises(NotFound) as e:
        handler, arguments = await coro

    assert e.value.code == 404

    error_handler = await router.get_error_handler(404)
    res = await error_handler(tygs_request, tygs_request.response)
    assert res.render_response()['body'] == "Unknown Error".encode('utf8')


@pytest.mark.asyncio
async def test_queued_webapp_and_client(queued_webapp):

    app = queued_webapp()
    http = app.components['http']

    @http.get('/')
    def zero_error(req, res):
        1 / 0

    await app.async_ready()
    response = await app.client.get('/')
    assert response.status_code == 500
    assert response.reason == 'Internal server error'
    assert 'ZeroDivisionError: division by zero' in response._renderer_data
    await app.async_stop()
