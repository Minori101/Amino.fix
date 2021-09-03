__title__ = 'Amino.fix'
__author__ = 'Minori'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020-2021 Minori'
__version__ = '1.0.0'

from .client import Client
from .lib.util import objects, exceptions
from .socket import Callbacks, SocketHandler
from requests import get
from json import loads

__newest__ = loads(get("https://test.pypi.org/pypi/amino.fix/json").text)["info"]["version"]

if __version__ != __newest__:
    print(f"New version of {__title__} available: {__newest__} (Using {__version__})")
    print(f"To update to the latest version, write to pip this command - pip install fixed.lib=={__newest__}")