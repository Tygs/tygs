
import pytest

from tygs.http.server import Router, HttpRequestController


@pytest.mark.asyncio
async def test_aiohttp_request(app, aiohttp_request):
    router = Router()

    def toto(req, res):
        assert req.headers['foo'] == 'bar'

    router.add_route('/toto', 'toto_url', toto)

    req = aiohttp_request('GET', "/toto", headers={'foo': 'bar'})
    tygs_request = HttpRequestController(app, req)
    handler, arguments = await router.get_handler(tygs_request)
    toto(tygs_request, tygs_request.response)
