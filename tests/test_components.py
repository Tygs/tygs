import asyncio
import pytest
from unittest.mock import MagicMock

import jinja2

from tygs import components, app
from tygs.test_utils import AsyncMock

from tygs.app import App


def test_component():
    c = components.Component('bla')
    assert c.app == 'bla'


@pytest.mark.asyncio
async def test_signal_dispatcher():
    s = components.SignalDispatcher(App('test'))
    assert s.signals == {}

    amock = AsyncMock()
    amock2 = AsyncMock()
    amock3 = AsyncMock()

    handler = amock()
    handler2 = amock2()
    handler3 = amock3()

    s.register('wololo', handler)

    assert len(s.signals) == 1
    assert handler in s.signals['wololo']

    s.register('event', handler2)
    assert len(s.signals) == 2
    assert handler2 in s.signals['event']

    # Using the same name add an handler to the list of handlers for this event
    s.register('wololo', handler3)

    assert len(s.signals) == 2
    assert len(s.signals['wololo']) == 2
    assert handler3 in s.signals['wololo']
    assert handler in s.signals['wololo']

    await s.trigger('wololo')

    amock.assert_called_once_with()
    amock3.assert_called_once_with()
    assert amock2.call_count == 0


def test_signal_dispatcher_decorator():
    s = components.SignalDispatcher(App('test'))
    s.register = MagicMock()

    mock = AsyncMock()
    mock = s.on('event')(mock)

    s.register.assert_called_once_with('event', mock)


@pytest.mark.asyncio
async def test_jinja2_renderer():
    my_app = app.App('test')

    print("app", id(my_app))
    print("dispatcher", id(my_app.components['signals']))
    print("handlers", id(my_app.components['signals'].signals))

    my_app.components['renderer'] = components.Jinja2Renderer(my_app)

    import ipdb; ipdb.set_trace()

    my_app.project_dir = MagicMock()
    await my_app.async_ready()

    assert hasattr(my_app.components['renderer'], 'env')
    assert isinstance(my_app.components['renderer'].env.loader,
                      jinja2.FileSystemLoader)
    assert my_app.components['renderer'].env.autoescape

    await my_app.async_stop()
