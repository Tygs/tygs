
import pytest

from unittest.mock import MagicMock, patch, Mock

from tygs.app import App
from tygs.components import SignalDispatcher
from .async_mock import AsyncMock


@pytest.fixture
def app():

    app = App("namespace")
    signal_mock = MagicMock(app.components['signals'])
    app.components['signals'] = signal_mock
    return app


def test_basic_api(app):
    assert app.ns == "namespace"
    assert isinstance(app.components['signals'], SignalDispatcher)
    assert app.project_dir is None


def test_event_wrappers(app):

    @app.on('event')
    def toto():
        pass

    app.components['signals'].on.assert_called_once_with('event')

    app.trigger('event')

    app.components['signals'].trigger.assert_called_once_with('event')


@pytest.mark.asyncio
async def test_ready(app):

    app.setup_lifecycle = AsyncMock()
    app.ready('project_dir')
    app.setup_lifecycle.assert_called_once_with()
    assert app.project_dir == "project_dir"


@pytest.mark.asyncio
async def test_ready_cwd(app):
    with patch('tygs.utils.get_project_dir'):
        app.ready()
        assert isinstance(app.project_dir, Mock)
