import pytest

from unittest.mock import MagicMock

from tygs.webapp import WebApp
from tygs.app import App


@pytest.fixture
def webapp():
    app = WebApp("namespace")
    return app


@pytest.fixture
def app_with_mocked_signal_dispatcher():

    app = App("namespace")
    signal_mock = MagicMock(app.components['signals'])
    app.components['signals'] = signal_mock
    return app


@pytest.fixture
def app():

    app = App("namespace")
    return app
