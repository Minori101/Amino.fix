import json

from functools import reduce
from base64 import b64decode
from typing import Union
import requests

session = requests.Session()

def generate_device_info() -> dict:

    return {
        "device_id": deviceId(),
        "user_agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G965N Build/star2ltexx-user 7.1.; com.narvii.amino.master/3.4.33602)"
    }

def deviceId(data: str = None) -> str:
    if data == None:
        response = session.get(f"https://ed-generators.herokuapp.com/device")
    else:
        response = session.get(f"https://ed-generators.herokuapp.com/device?data={data}")
    return response.text.upper()

#@dorthegra/IDörthe#8835 the server was bought with his money :p you can write to him to thank you 
def signature(data: Union[str, dict]) -> str:
    response = session.post("https://ed-generators.herokuapp.com/signature", data=data)
    return response.text

def update_deviceId(deviceId: str) -> str:
    response = session.get(f"https://ed-generators.herokuapp.com/update-device?device={deviceId}")
    return response.text

def decode_sid(sid: str) -> dict:
    return json.loads(b64decode(reduce(lambda a, e: a.replace(*e), ("-+", "_/"), sid + "=" * (-len(sid) % 4)).encode())[1:-20].decode())

def sid_to_uid(SID: str) -> str: return decode_sid(SID)["2"]

def sid_to_ip_address(SID: str) -> str: return decode_sid(SID)["4"]