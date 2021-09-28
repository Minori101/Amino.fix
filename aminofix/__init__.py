__title__ = 'Amino.fix'
__author__ = 'Minori'
__license__ = 'MIT'
__copyright__ = 'Copyright 2020-2021 Minori'
__version__ = '1.2.18.1'

from .acm import ACM
from .client import Client
from .sub_client import SubClient
from .lib.util import device, exceptions, helpers, objects, headers
from requests import get
from json import loads

__newest__ = loads(get("https://pypi.org/pypi/amino.fix/json").text)["info"]["version"]

if __version__ != __newest__:
    print(f"New version of {__title__} available: {__newest__} (Using {__version__})")
    print(f"To update to the latest version, write to pip this command - pip install --upgrade amino.fix")
    print("Discord link - https://discord.gg/Bf3dpBRJHj")