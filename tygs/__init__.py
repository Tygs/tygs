
from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution('tygs').version
except DistributionNotFound:
    __version__ = ('Unable to read this module metadata. ',
                   'Check manually the setup.py file for version.')

from tygs.core import *