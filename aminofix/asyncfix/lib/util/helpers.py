import base64
import hmac
import json

from hashlib import sha1
from functools import reduce
from base64 import b64decode
from typing import Union
import requests
import random
import string

from aminofix import client

def generate_device_info() -> dict:

    data = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + "_-", k=462)).replace("--", "-")
    device = deviceId(data)

    return {
        "device_id": device,
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G965N Build/star2ltexx-user 7.1.; com.narvii.amino.master/3.4.33592)"
    }

def deviceId(data: str) -> str:
    response = client.session.get(f"https://ed-generators.herokuapp.com/device?data={data}")
    return response.text

def signature(data: Union[str, dict]) -> str:
    response = client.session.get(f"https://ed-generators.herokuapp.com/signature?data={data}")
    return response.text

def update_deviceId(deviceId: str) -> str:
    response = client.session.get(f"https://ed-generators.herokuapp.com/update-device?device={deviceId}")
    return response.text

def decode_sid(sid: str) -> dict:
    return json.loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())

def sid_to_uid(SID: str) -> str: return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str: return decode_sid(SID)["4"]
