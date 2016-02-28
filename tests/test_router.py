
import pytest

from tygs.http.server import Router, HttpRequestController

from werkzeug.routing import Map
from werkzeug.exceptions import NotFound

from .test_utils import aiorun


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


def test_get_handler(app, aiohttp_request):
    router = Router()

    def toto():
        pass

    router.add_route('/toto', 'toto_url', toto)

    req = aiohttp_request('GET', "/toto")
    tygs_request = HttpRequestController(app, req)
    coro = router.get_handler(tygs_request)
    handler, arguments = aiorun(coro)


def test_get_handler_404(app, aiohttp_request):
    router = Router()

    def toto():
        pass

    router.add_route('/toto', 'toto_url', toto)

    req = aiohttp_request('GET', "/tata")
    tygs_request = HttpRequestController(app, req)
    coro = router.get_handler(tygs_request)

    with pytest.raises(NotFound) as e:
        handler, arguments = aiorun(coro)

    assert e.value.code == 404
