
import pytest

from unittest.mock import Mock, MagicMock, patch

from aiohttp.web import Application

from tygs.test_utils import AsyncMock
from tygs.webapp import WebApp
from tygs.components import SignalDispatcher, HttpComponent, Jinja2Renderer
from tygs.http.server import Server


def test_basic_api(webapp):

    assert webapp.ns == "namespace"
    assert isinstance(webapp.components['signals'], SignalDispatcher)
    assert isinstance(webapp.components['http'], HttpComponent)
    assert isinstance(webapp.components['templates'], Jinja2Renderer)
    assert webapp.project_dir is None
    assert isinstance(webapp._aiohttp_app, Application)


def test_event_wrappers():

    with patch('tygs.app.SignalDispatcher'):

        webapp = WebApp("namespace")

        @webapp.on('event')
        def toto():  # pragma: no cover
            pass

        webapp.components['signals'].on.assert_called_once_with('event')

        webapp.trigger('event')

        webapp.components['signals'].trigger.assert_called_once_with('event')


def test_quickstart(webapp):
    app, http = WebApp.quickstart("namespace")
    assert isinstance(app, WebApp)
    assert http is app.components['http']


@pytest.mark.asyncio
async def test_ready():
    webapp = WebApp("namespace", server_class=Mock())

    ensure_init = AsyncMock()
    webapp.register('init', ensure_init)

    ensure_ready = MagicMock()

    @webapp.on('running')
    async def func():
        webapp.http_server.start.assert_called_once_with()
        ensure_init.assert_called_once_with()
        assert webapp.project_dir == "project_dir"
        ensure_ready()

    running_future = await webapp.async_ready('project_dir')
    await running_future
    await webapp.async_stop()
    ensure_ready.assert_called_once_with()


@pytest.mark.asyncio
async def test_ready_project_dir(webapp):

    with patch('tygs.app.get_project_dir'):
        await webapp.async_ready()
        from tygs.app import get_project_dir
        get_project_dir.assert_called_once_with()
        await webapp.async_stop()


@pytest.mark.asyncio
async def test_error_in_ready():

    class FailingServer(Server):

        def __init__(self, *args, **kwargs):
            raise RuntimeError('This should fail unconditionally')

    app = WebApp('namespace', server_class=FailingServer)

    try:  # prevents the error from cascading, so we can easily find out what
        # it breaks
        with pytest.raises(RuntimeError):
            await app.async_ready()
    finally:
        await app.async_stop()
