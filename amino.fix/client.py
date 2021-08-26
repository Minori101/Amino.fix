import aiohttp
import requests
import hmac
import json
import base64
from hashlib import sha1
import time
from time import time as timestamp
from time import timezone, sleep
from typing import BinaryIO
import concurrent.futures
import asyncio

from objects import ThreadList
from objects import Thread
from objects import GetMessages
from objects import Message

import random
import string

#gen_msg_sig by SirLez with Bovonos 
def gen_msg_sig():
    return base64.b64encode(bytes.fromhex("22") + hmac.new(bytes.fromhex(str(int(time.time()))), "22".encode("utf-8"),
                                                           sha1).digest()).decode()
#generate captcha from samino
def captcha():
        captcha = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + "_-", k=462)).replace("--", "-")
        return captcha

class Client:
    def __init__(self, deviceId: str, profile: str = None, certificatePath = None):
        self.api = 'https://service.narvii.com/api/v1'
        self.configured = None

        self.sid = None
        self.certificatePath = certificatePath
        self.profile = profile
        self.auid = None
        self.headers = {
            "NDCLANG": "ru",
            "NDC-MSG-SIG": gen_msg_sig(),
            "NDCDEVICEID": f"{deviceId}",
            "SMDEVICEID": "b89d9a00-f78e-46a3-bd54-6507d68b343c",
            "NDCAUTH": f"sid={self.sid}",
            "Accept-Language": "ru-RU",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G977N Build/beyond1qlteue-user 7; com.narvii.amino.master/3.4.33578)",
            "Host": "service.narvii.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }
        self.web_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "x-requested-with": "xmlhttprequest"
        }
        self.device_id = deviceId
        self.userId = None
        self.comId = None
        self.json = None
        self.uid = None
    def web_login(self, email: str, password: str):
        data = {
            "auth_type": 0,
            "email": email,
            "recaptcha_challenge": captcha(),
            "recaptcha_version": "v3",
            "secret": password
        }
        response = requests.post("https://aminoapps.com/api/auth", json=data)
        if response.status_code != 200:
            print(json.loads(response.text))
        else:
            self.web_headers = response.headers
            print(response.headers)
            self.sid = response.headers["set-cookie"]
            try: 
                self.sid = self.sid[0: self.sid.index(";")]
            except: 
                self.sid = self.sid
            self.uid = response.json()["result"]["uid"]
            self.headers["NDCAUTH"] = self.sid
            if self.profile != None:
                try:
                    self.userId = self.get_chat_id(code=self.profile)['chatId']
                    self.comId = self.get_chat_id(code=self.profile)['comId']
                except:
                    self.profile = None
            return response.status_code
    def get_chat_id(self, code: str):
        url = f"{self.api}/g/s/link-resolution?q={code}"
        response = requests.get(url=url, headers=self.headers).json()['linkInfoV2']['extensions']['linkInfo']
        return {"comId": response['ndcId'], "chatId": response['objectId']}

    def join_community(self, comId: str, invitationId: str = None):
        url = f"{self.api}/x{comId}/s/community/join"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.post(url=url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200:
            print(json.loads(response.text))
        else:
            return response.status_code
    def leave_community(self, comId: str):
        url = f"{self.api}/x{comId}/s/community/leave"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.post(url=url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200:
            print(json.loads(response.text))
        else:
            return response.status_code
    def get_user_info(self, userId: str):
        url = f"{self.api}/g/s/user-profile/{userId}"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(url=url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200:
            print(json.loads(response.text))
        else:
            return objects.UserProfile(json.loads(response.text)["userProfile"]).UserProfile
    def get_from_deviceid(self, deviceId: str):
        url=f"{self.api}/g/s/auid?deviceId={deviceId}"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(url=url, verify=self.certificatePath)
        if response.status_code != 200:
            print(json.loads(response.text))
        else: 
            return json.loads(response.text)["auid"]
    def join_chat(self, chatId: str):
        url = f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.post(url=url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200:
            print(json.loads(response.text))
        else: 
            return json.loads(response.text)
    def leave_chat(self, chatId: str):
        url = f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.delete(url=url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200:
            print(json.loads(response.text))
        else: 
            return json.loads(response.text)
    def start_chat(self, userId: [str, list], message: str, title: str = None, content: str = None, isGlobal: bool = False, publishToGlobal: bool = False):
        url=f"{self.api}/g/s/device/dev-options"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(url=url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return response.status_code
        url=f"{self.api}/g/s/chat/thread-check/human-readable?ndcIds=0%2C54623866"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(url=url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return response.status_code
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise exceptions.WrongType()

        data = {
            "type": title,
            "inviteeUids": [userIds],
            "initialMessageContent": message,
            "content": content,
            "timestamp": int(timestamp() * 1000)
        }

        if isGlobal is True: data["type"] = 2; data["eventSource"] = "GlobalComposeMenu"
        else: data["type"] = 0

        if publishToGlobal is True: data["publishToGlobal"] = 1
        else: data["publishToGlobal"] = 0

        data = json.dumps(data)
        url= f"{self.api}/x{comId}/s/chat/thread"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.post(url=url, data=data, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return response.status_code
    def comment(self, message: str, userId: str = None, blogId: str = None, wikiId: str = None, replyTo: str = None):
        if message is None: raise exceptions.MessageNeeded

        data = {
            "content": message,
            "stickerId": None,
            "type": 0,
            "timestamp": int(timestamp() * 1000)
        }

        if replyTo: data["respondTo"] = replyTo

        if userId:
            data["eventSource"] = "UserProfileView"
            data = json.dumps(data)
            self.headers["NDC-MSG-SIG"] = gen_msg_sig()
            response = requests.post(f"{self.api}/g/s/user-profile/{userId}/g-comment", headers=self.headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        elif blogId:
            data["eventSource"] = "PostDetailView"
            data = json.dumps(data)
            self.headers["NDC-MSG-SIG"] = gen_msg_sig()
            response = requests.post(f"{self.api}/g/s/blog/{blogId}/g-comment", headers=self.headers, data=data, verify=self.certificatePath)

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = json.dumps(data)
            self.headers["NDC-MSG-SIG"] = gen_msg_sig()
            response = requests.post(f"{self.api}/g/s/item/{wikiId}/g-comment", headers=self.headers, data=data, verify=self.certificatePath)

        else: 
            print('Bruh')
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return response.status_code
    def invite_to_chat(self, userId: [str, list], chatId: str):
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise exceptions.WrongType
        data = json.dumps({
            "uids": userIds,
            "timestamp": int(timestamp() * 1000)
        })
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get("https://service.narvii.com/api/v1/g/s/chat/thread-check/human-readable?ndcIds=0%2C54623866", headers=self.headers)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return response1.status_code
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.post(f"{self.api}/g/s/chat/thread/{chatId}/member/invite", headers=self.headers, data=data, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return response.status_code
    def send_message(self, chatId: str, message: str = None, messageType: int = 0, file: BinaryIO = None, fileType: str = None, replyTo: str = None, mentionUserIds: list = None, stickerId: str = None, embedId: str = None, embedType: int = None, embedLink: str = None, embedTitle: str = None, embedContent: str = None, embedImage: BinaryIO = None):
        """
        **Parameters**
            - **message** : Message to be sent
            - **chatId** : ID of the Chat.
            - **file** : File to be sent.
            - **fileType** : Type of the file.
                - ``audio``, ``image``, ``gif``
            - **messageType** : Type of the Message.
            - **mentionUserIds** : List of User IDS to mention. '@' needed in the Message.
            - **replyTo** : Message ID to reply to.
            - **stickerId** : Sticker ID to be sent.
            - **embedTitle** : Title of the Embed.
            - **embedContent** : Content of the Embed.
            - **embedLink** : Link of the Embed.
            - **embedImage** : Image of the Embed.
            - **embedId** : ID of the Embed.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """

        if message is not None and file is None:
            message = message.replace("<$", "‎‏").replace("$>", "‬‭")

        mentions = []
        if mentionUserIds:
            for mention_uid in mentionUserIds:
                mentions.append({"uid": mention_uid})

        if embedImage:
            embedImage = [[100, self.upload_media(embedImage, "image"), None]]

        data = {
            "type": messageType,
            "content": message,
            "clientRefId": int(timestamp() / 10 % 1000000000),
            "attachedObject": {
                "objectId": embedId,
                "objectType": embedType,
                "link": embedLink,
                "title": embedTitle,
                "content": embedContent,
                "mediaList": embedImage
            },
            "extensions": {"mentionedArray": mentions},
            "timestamp": int(timestamp() * 1000)
        }

        if replyTo: data["replyMessageId"] = replyTo

        if stickerId:
            data["content"] = None
            data["stickerId"] = stickerId
            data["type"] = 3

        if file:
            data["content"] = None
            if fileType == "audio":
                data["type"] = 2
                data["mediaType"] = 110

            elif fileType == "image":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/jpg"
                data["mediaUhqEnabled"] = True

            elif fileType == "gif":
                data["mediaType"] = 100
                data["mediaUploadValueContentType"] = "image/gif"
                data["mediaUhqEnabled"] = True

            else: raise exceptions.SpecifyType(fileType)

            data["mediaUploadValue"] = base64.b64encode(file.read()).decode()

        data = json.dumps(data)
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.post(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/message", headers=self.headers, data=data, verify=self.certificatePath)
        if response.status_code != 200: 
            return print(json.loads(response.text))
        else: 
            return response.status_code
    def get_chat_threads(self, start: int = 0, size: int = 25):
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(f"{self.api}/g/s/chat/thread?type=joined-me&start={start}&size={size}", headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return ThreadList(json.loads(response.text)["threadList"]).ThreadList
    def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None):
        """
        List of Messages from an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - *size* : Size of the list.
            - *size* : Size of the list.
            - *pageToken* : Next Page Token.

        **Returns**
            - **Success** : :meth:`Message List <amino.lib.util.objects.MessageList>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        if pageToken is not None: url = f"{self.api}/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&pageToken={pageToken}&size={size}"
        else: url = f"{self.api}/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(url, headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return GetMessages(json.loads(response.text)).GetMessages
    def get_message_info(self, chatId: str, messageId: str):
        """
        Information of an Message from an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - **messageId** : ID of the Message.

        **Returns**
            - **Success** : :meth:`Message Object <amino.lib.util.objects.Message>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(f"{self.api}/g/s/chat/thread/{chatId}/message/{messageId}", headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            return Message(json.loads(response.text)["message"]).Message
    def login(self, email: str, password: str):
        data1 = json.dumps({
            "email": email,
            "v": 2,
            "secret": f"0 {password}",
            "deviceID": f"{self.device_id}",
            "clientType": 100,
            "action": "normal",
            "timestamp": int(timestamp() * 1000)
        })
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.post(f"{self.api}/g/s/auth/login", headers=self.headers_login, data=data1, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            self.json = json.loads(response.text)
            self.sid = self.json["sid"]
    def get_chat_thread(self, chatId: str):
        """
        Get the Chat Object from an Chat ID.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : :meth:`Chat Object <amino.lib.util.objects.Thread>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        self.headers["NDC-MSG-SIG"] = gen_msg_sig()
        response = requests.get(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}", headers=self.headers, verify=self.certificatePath)
        if response.status_code != 200: 
            print(json.loads(response.text))
        else: 
            print(Thread(json.loads(response.text)["thread"]).Thread)
#lib by Plevanto and Morg (fix Amino.py 1.2.17)
#invite_to_chat, start_chat, get_chat_thread not working
#https://service.narvii.com/api/v1/g/s/chat/thread-check/human-readable?ndcIds=0%2C54623866 - ?