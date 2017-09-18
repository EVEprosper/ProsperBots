"""commands.py: generic responses for bots.  We make the responses"""
from os import path
import platform

from . import _version
from . import connections
from . import utils
from . import exceptions
from . import config as api_config

HERE = path.abspath(path.dirname(__file__))

def version_info(app_name):
    """return version string for status checker

    Args:
        app_name (str): name of bot structure

    Returns:
        (str): {app_name} -- {version} -- {platform.node()}

    """
    return '{app_name} -- {version} -- {platform}'.format(
        app_name=app_name,
        version=_version.__version__,
        platform=platform.node()
    )
