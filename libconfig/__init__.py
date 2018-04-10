# pylint: disable-msg=W0614,W0401,W0611,W0622

# flake8: noqa

"""A small library for global parameter configuration.

.. moduleauthor:: Jaume Bonet <jaume.bonet@gmail.com>

"""


from .config import *

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
