import asyncio
import pytest

from unittest.mock import MagicMock, patch, Mock

from tygs import components
from .async_mock import AsyncMock


def test_component():
    c = components.Component('bla')
    assert c.app == 'bla'


@pytest.mark.asyncio
async def test_signal_dispatcher():
    s = components.SignalDispatcher()
    assert s.signals == {}

    handler = AsyncMock()
    handler2 = AsyncMock()
    handler3 = AsyncMock()

    s.register('wololo', handler)

    assert len(s.signals) == 1
    assert handler in s.signals['wololo']

    s.register('event', handler2)
    assert len(s.signals) == 2
    assert handler2 in s.signals['event']

    s.register('wololo', handler3)

    assert len(s.signals) == 2
    assert len(s.signals['wololo']) == 2
    assert handler3 in s.signals['wololo']
    assert handler in s.signals['wololo']

    handlers = await asyncio.gather(*s.trigger('wololo'))

    handler.assert_called_once_with()
    handler3.assert_called_once_with()
    assert handler2.call_count == 0


def test_signal_dispatcher_decorator():
    s = components.SignalDispatcher()
    s.register = MagicMock()

    handler = AsyncMock()

    handler = s.on('event')(handler)

    s.register.assert_called_once_with('event', handler)
