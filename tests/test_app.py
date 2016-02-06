import pytest

from unittest.mock import patch, MagicMock

from tygs.components import SignalDispatcher
from tygs.test_utils import AsyncMock


from . import fixtures

app = fixtures.app
app_with_mocked_signal_dispatcher = fixtures.app_with_mocked_signal_dispatcher


def test_basic_api(app):
    assert app.ns == "namespace"
    assert isinstance(app.components['signals'], SignalDispatcher)
    assert app.project_dir is None


def test_event_wrappers(app_with_mocked_signal_dispatcher):

    app = app_with_mocked_signal_dispatcher

    @app.on('event')
    def toto():  # pragma: no cover
        pass

    app.components['signals'].on.assert_called_once_with('event')

    app.trigger('event')

    app.components['signals'].trigger.assert_called_once_with('event')


@pytest.mark.asyncio
async def test_async_ready(app):

    app.setup_lifecycle = AsyncMock()

    await app.async_ready('project_dir')
    app.setup_lifecycle.assert_called_once_with()
    await app.async_stop()


@pytest.mark.asyncio
async def test_async_ready_lifecycle(app):

    ensure_init = AsyncMock()
    app.register('init', ensure_init())

    ensure_ready = MagicMock()

    @app.on('running')
    async def func():
        ensure_init.assert_called_once_with()
        assert app.project_dir == "project_dir"
        ensure_ready()

    task = await app.async_ready('project_dir')
    await task  # TODO: create app.after('running') feature
    await app.async_stop()
    ensure_ready.assert_called_once_with()


@pytest.mark.asyncio
async def test_async_ready_cwd(app):
    with patch('tygs.app.get_project_dir'):
        await app.async_ready()
        from tygs.app import get_project_dir
        get_project_dir.assert_called_once_with()
        await app.async_stop()
