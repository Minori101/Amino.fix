from aminofix.lib.util import device

sid = None

gen_msg_sig = None

class Headers:
    def __init__(self, data = None, type = None, deviceId: str = None, sig: str = None):
        if deviceId:
            dev = device.DeviceGenerator(deviceId=deviceId)
        else:
            dev = device.DeviceGenerator()

        headers = {
            "NDCLANG": "en",
            "NDC-MSG-SIG": gen_msg_sig,
            "NDCDEVICEID": dev.device_id,
            "SMDEVICEID": "b89d9a00-f78e-46a3-bd54-6507d68b343c",
            "NDCAUTH": f"sid={sid}",
            "Accept-Language": "en-US",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": dev.user_agent,
            "Host": "service.narvii.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip"
        }

        s_headers = {"NDCDEVICEID": dev.device_id}

        web_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "x-requested-with": "xmlhttprequest"
        }

        if data: headers["Content-Length"] = str(len(data))
        if sid: headers["NDCAUTH"] = f"{sid}"
        if sid: s_headers["NDCAUTH"] = f"{sid}"
        if type: headers["Content-Type"] = type
        if sig: headers["NDC-MSG-SIG"] = sig
        if web: web_headers = web
        self.headers = headers
        self.s_headers = s_headers
        self.web_headers = web_headers