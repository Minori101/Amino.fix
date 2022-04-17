import json
import os

from functools import reduce
from base64 import b64decode, b64encode
from typing import Union
from hashlib import sha1
from hmac import new

PREFIX = bytes.fromhex("42")
SIG_KEY = bytes.fromhex("F8E7A61AC3F725941E3AC7CAE2D688BE97F30B93")
DEVICE_KEY = bytes.fromhex("02B258C63559D8804321C5D5065AF320358D366F")

def generate_device_info() -> dict:

    return {
        "device_id": deviceId(),
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G965N Build/star2ltexx-user 7.1.; com.narvii.amino.master/3.4.33602)"
    }

def deviceId(data: bytes = None) -> str:
    if isinstance(data, str): data = bytes(data, 'utf-8')
    identifier = PREFIX + (data or os.urandom(20))
    mac = new(DEVICE_KEY, identifier, sha1)
    return f"{identifier.hex()}{mac.hexdigest()}".upper()

def signature(data: Union[str, bytes]) -> str:
    data = data if isinstance(data, bytes) else data.encode("utf-8")
    return b64encode(PREFIX + new(SIG_KEY, data, sha1).digest()).decode("utf-8")

def update_deviceId(device: str) -> str:
    return deviceId(bytes.fromhex(device[2:42]))

def decode_sid(sid: str) -> dict:
    return json.loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())

def sid_to_uid(SID: str) -> str: return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str: return decode_sid(SID)["4"]