import json

from hashlib import sha1
from functools import reduce
from base64 import b85decode, b64decode


def generate_device_info():
    try:
        deviceId = "221EAE9F9C08B08EA4F632F4C397847FC606A4BCD2E449B175997630041414E121C54063A5EC0E02C8"
    except Exception:
        deviceId = "221EAE9F9C08B08EA4F632F4C397847FC606A4BCD2E449B175997630041414E121C54063A5EC0E02C8"

    return {
        "device_id": deviceId,
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G977N Build/beyond1qlteue-user 7; com.narvii.amino.master/3.4.33578)"
    }

# okok says: please use return annotations :(( https://www.python.org/dev/peps/pep-3107/#return-values

def decode_sid(sid: str) -> dict:
    return json.loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())

def sid_to_uid(SID: str) -> str: return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str: return decode_sid(SID)["4"]