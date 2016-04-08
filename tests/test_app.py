import pytest
import warnings
import subprocess
import sys
import time

from unittest.mock import patch, MagicMock, Mock

from tygs.components import SignalDispatcher
from tygs.test_utils import AsyncMock
from tygs.utils import aioloop as get_loop, DebugException


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
    app.setup = AsyncMock()
    await app.async_ready('project_dir')
    app.setup.assert_called_once_with('project_dir')
    await app.async_stop()


def test_ready(aioloop, app):
    beacon = Mock()

    @app.on('running')
    def stahp():
        beacon()
        app.stop()

    app.ready()
    beacon.assert_called_once_with()


def test_ready_with_cwd(aioloop, app):
    beacon = Mock()

    @app.on('running')
    def stahp():
        beacon()
        app.stop()

    app.ready('test/cwd')
    beacon.assert_called_once_with()
    assert app.project_dir == 'test/cwd'


def test_stop_outside_loop(aioloop, app):
    aioloop.close()
    app.stop()


def test_ready_with_closed_loop(aioloop, app):
    aioloop.close()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(RuntimeError):
            app.ready()


@pytest.mark.asyncio
async def test_ready_in_loop(app):
    with pytest.raises(RuntimeError):
        app.ready()


# aioloop make sure we have a fresh loop to start with event if py.test closed
# the previous one
def test_ready_keyboard_interrupt(aioloop, app):
    beacon = Mock()
    real_stop = app._finish

    def beacon_stop():
        beacon()
        real_stop()

    app._finish = beacon_stop

    @app.on('running')
    def stahp():
        beacon()
        raise KeyboardInterrupt()

    @app.on('stop')
    def stop():
        beacon()

    app.ready()

    assert beacon.call_count == 3


def test_ready_sigterm():
    shell = subprocess.Popen([sys.executable, 'tests/tygs_process'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    time.sleep(1)
    shell.terminate()
    stderr = shell.stderr.read()
    return_code = shell.wait()
    assert stderr == b''
    assert return_code == 0


@pytest.mark.asyncio
async def test_async_ready_setup(app):

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


def test_ready_closed_loop(aioloop, app):
    aioloop.close()
    with pytest.raises(RuntimeError):
        app.ready()


def test_ready_running_loop(aioloop, app):

    async def start():
        app.ready()

    with pytest.raises(RuntimeError):
        aioloop.run_until_complete(start())


def test_forbid_finish(aioloop, app):

    @app.on('running')
    def stahp():
        app._finish()

    with pytest.raises(RuntimeError):
        app.ready()


def test_stop(aioloop, app):

    @app.on('running')
    def stop():
        app.stop()

    app.ready()

    # calling _finish() after stop() is a no op
    app._finish()
    # calling stop() again after stop() is a no op
    app.stop()


@pytest.mark.asyncio
async def test_stop_twice(app):
    await app.async_ready()
    await app.async_stop()
    app.stop()


def test_fail_fast_mode(aioloop, app):

    with pytest.raises(Exception):
        app.fail_fast(True)

        @app.on('running')
        def stahp():
            raise Exception('Breaking the loop')

        app.ready()


def test_fail_fast_mode_disable(aioloop, app):

    app.fail_fast(True)
    assert DebugException.fail_fast_mode

    @app.on('running')
    def stahp():
        raise Exception('Breaking the loop')

    with pytest.raises(Exception):
        app.ready()

    app.fail_fast(False)
    assert DebugException.old_factory is None
    assert not DebugException.fail_fast_mode

    app.fail_fast(False)  # this is a noop
    assert DebugException.old_factory is None
    assert not DebugException.fail_fast_mode

    # refresh the loop
    app.loop = get_loop()

    # TODO: write an app.restart() method ?

    @app.on('running')
    def non_stop():
        raise Exception('Breaking the loop')

    @app.on('running')
    def stop():
        app.stop()

    app.ready()





