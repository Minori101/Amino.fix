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

def generate_device_info() -> dict:

    data = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + "_-", k=462)).replace("--", "-")
    device = deviceId(data)

    return {
        "device_id": device,
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G965N Build/star2ltexx-user 7.1.; com.narvii.amino.master/3.4.33592)"
    }

# okok says: please use return annotations :(( https://www.python.org/dev/peps/pep-3107/#return-values

def deviceId(data):
    uids = str(data)
    return ("32" + sha1(uids.encode()).digest().hex() + hmac.new(bytes.fromhex("76b4a156aaccade137b8b1e77b435a81971fbd3e"), b'\x32' + sha1(uids.encode()).digest(), sha1).hexdigest()).upper()

def signature(data: Union[str, dict]) -> str:
    if isinstance(data, dict): data = json.dumps(data)
    response = requests.get(f"http://aminoed.uk.to/api/generator/ndc-msg-sig?data={data}").json()
    return response["message"]

def decode_sid(sid: str) -> dict:
    return json.loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())

def sid_to_uid(SID: str) -> str: return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str: return decode_sid(SID)["4"]
