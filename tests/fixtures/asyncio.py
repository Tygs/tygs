
import pytest

from tygs.utils import aioloop as get_loop


@pytest.yield_fixture
def aioloop():
    """ Ensure there is an opened event loop available and return it"""

    loop = get_loop()
    yield loop
    loop.close()
