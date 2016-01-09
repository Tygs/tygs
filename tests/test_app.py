
import pytest

from unittest.mock import MagicMock, patch, Mock

from tygs.app import App
from tygs.components import SignalDispatcher


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


def test_ready(app):

    app.ready('project_dir')
    app.components['signals'].trigger.assert_called_once_with('ready')
    assert app.project_dir == "project_dir"

    with patch('tygs.utils.get_project_dir'):
        app.ready()
        assert isinstance(app.project_dir, Mock)

