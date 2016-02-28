
import asyncio

import pytest


@pytest.fixture
def aioloop():
    """ Ensure they is an opened event loop available and return it"""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        policy = asyncio.get_event_loop_policy()
        loop = policy.new_event_loop()
        policy.set_event_loop(loop)
    return loop


