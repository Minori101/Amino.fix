import base64
import hmac
import json

from hashlib import sha1
from functools import reduce
from base64 import b64decode
from typing import Union


def generate_device_info() -> dict:
    return {
        "device_id": "221EAE9F9C08B08EA4F632F4C397847FC606A4BCD2E449B175997630041414E121C54063A5EC0E02C8",
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G977N Build/beyond1qlteue-user 7; com.narvii.amino.master/3.4.33578)"
    }

# okok says: please use return annotations :(( https://www.python.org/dev/peps/pep-3107/#return-values

def signature(data: Union[str, dict]) -> str:
    if isinstance(data, dict): data = json.dumps(data)
    mac = hmac.new(bytes.fromhex("307c3c8cd389e69dc298d951341f88419a8377f4"), data.encode("utf-8"), sha1)
    digest = bytes.fromhex("22") + mac.digest()
    return base64.b64encode(digest).decode("utf-8")

def decode_sid(sid: str) -> dict:
    return json.loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())

def sid_to_uid(SID: str) -> str: return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str: return decode_sid(SID)["4"]
