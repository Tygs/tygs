
import pytest

from unittest.mock import MagicMock, patch, Mock

from aiohttp.web import Application

from tygs.webapp import WebApp
from tygs.components import SignalDispatcher, HttpComponent, Jinja2Renderer


@pytest.fixture
def app():

    app = WebApp("namespace")
    signal_mock = MagicMock(app.components['signals'])
    app.components['signals'] = signal_mock
    return app


def test_basic_api(app):
    assert app.ns == "namespace"
    assert isinstance(app.components['signals'], SignalDispatcher)
    assert isinstance(app.components['http'], HttpComponent)
    assert isinstance(app.components['templates'], Jinja2Renderer)
    assert app.project_dir is None
    assert isinstance(app._aiohttp_app, Application)


def test_event_wrappers(app):

    @app.on('event')
    def toto():
        pass

    app.components['signals'].on.assert_called_once_with('event')

    app.trigger('event')

    app.components['signals'].trigger.assert_called_once_with('event')


def test_quickstart(app):
    app, http = WebApp.quickstart("namespace")
    assert isinstance(app, WebApp)
    assert http is app.components['http']


@pytest.mark.asyncio
async def test_ready(app):

    with patch("tygs.webapp.Server"):
        app.ready('project_dir')

        @app.on('ready')
        def func():
            app.http_server.run.assert_called_once_with()

            app.http_server = MagicMock(app.http_server)
            app.components['signals'].trigger.assert_called_once_with('init')
            assert app.project_dir == "project_dir"


@pytest.mark.asyncio
async def test_ready_project_dir(app):

        with patch('tygs.app.get_project_dir'):
            app.ready()
            from tygs.app import get_project_dir
            get_project_dir.assert_called_once_with()
