
import inspect
from unittest.mock import patch, Mock

import pytest

from tygs import utils
from tygs.test_utils import AsyncMock


def test_get_project_dir():
    with patch('os.getcwd', new_callable=lambda: lambda: '/current/dir'):
        with patch('sys.argv') as argv:
            argv.__getitem__ = Mock(return_value='../path/to/wololo.py')
            cwd = utils.get_project_dir()
            assert cwd == '/current/path/to'


@pytest.mark.asyncio
async def test_async_mock():
    m = AsyncMock()
    await m('test')
    m.assert_called_once_with('test')


@pytest.mark.asyncio
async def test_asyncio_mock_with_await():
    m = AsyncMock()
    await m('test')
    m.assert_called_once_with('test')
    assert m.call_count == 1

    await m
    m.assert_called_with()
    assert m.call_count == 2


@pytest.mark.asyncio
async def test_ensure_awaitable():

    m = AsyncMock()

    def test():
        return m
    a = utils.ensure_awaitable(test)
    assert inspect.isawaitable(a)
    await a
    m.assert_called_once_with()

    m = AsyncMock()

    async def test():
        return await m
    a = utils.ensure_awaitable(test)
    assert inspect.isawaitable(a)
    await a
    m.assert_called_once_with()

    m = AsyncMock()

    async def test():
        return await m
    a = utils.ensure_awaitable(test())
    assert inspect.isawaitable(a)
    await a
    m.assert_called_once_with()

    with pytest.raises(TypeError):
        a = utils.ensure_awaitable("test()")


def test_register_exit_func():

    foo = Mock()
    bar = Mock()

    handler = utils.SigTermHandler()
    handler.register(foo)
    handler.register(bar)
    handler.register(bar)

    import pdb; pdb.set_trace()
    assert handler.signal_callbacks == {foo, bar}
