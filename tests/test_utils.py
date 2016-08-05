
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


def test_silence_loop_error_log(aioloop):
    assert aioloop._exception_handler is None
    with utils.silence_loop_error_log(aioloop):
        assert aioloop._exception_handler.__name__ == '<lambda>'
        assert aioloop._exception_handler(None, None) is None
        assert aioloop._exception_handler(1, {}) is None

    assert aioloop._exception_handler is None


def test_removable_property():

    m = Mock()

    class MyClass:

        @utils.removable_property
        def pwet(self):
            m()
            return 'method'

    my_class_instance = MyClass()
    assert m.call_count == 0
    assert my_class_instance.pwet == 'method'
    assert m.call_count == 1
    my_class_instance.pwet = 'value'
    assert my_class_instance.pwet == 'value'
    assert m.call_count == 1
    assert isinstance(MyClass.pwet, utils.removable_property)


@pytest.mark.asyncio
async def test_queued_webapp_and_client(queued_webapp):

    app = queued_webapp()
    http = app.components['http']

    # TODO: when 2 handlers have the same name, we create an endpoint with
    # the same name as well automatically, so it silently override each
    # other. We should check for duplicates and raise an exception instead.
    @http.get('/')
    def index_controller(req, res):
        return res.text('index_controller')

    await app.async_ready()
    response = await app.client.get('/')
    assert response._renderer_data == 'index_controller'
    await app.async_stop()


def test_aiorun():

    beacon = Mock()

    async def foo():
        beacon()
        return 1

    assert utils.aiorun(foo) == 1
    beacon.assert_called_once_with()
