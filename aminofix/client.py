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
from locale import getdefaultlocale as locale
from uuid import UUID, uuid4
import concurrent.futures
import asyncio

import random
import string

from .lib.util import exceptions, device, objects, helpers, headers

#not all functions work properly

device = device.DeviceGenerator()

class Client:
    def __init__(self, deviceId: str = None, proxies: dict = None, certificatePath = None, socket_trace = False, socketDebugging = False):
        self.api = 'https://service.narvii.com/api/v1'
        self.apip = 'https://aminoapps.com/api-p'
        self.configured = None

        if deviceId is not None: self.device_id = deviceId
        else: self.device_id = device.device_id
        self.user_agent = device.user_agent

        self.sid = None
        self.proxies = proxies
        self.certificatePath = certificatePath
        self.auid = None

        self.web_headers = headers.Headers().web_headers
        self.ad_headers = headers.AdHeaders().headers
        self.ad_data = headers.AdHeaders().data 

        self.userId = None
        self.comId = None
        self.json = None
        self.uid = None

    def login_sid(self, SID: str):
        """
        Login into an account with an SID

        **Parameters**
            - **SID** : SID of the account
        """
        uId = helpers.sid_to_uid(SID)
        SID1 = "sid="+SID
        self.sid = SID1
        self.userId = uId
        self.account: objects.UserProfile = self.get_user_info(uId)
        self.profile: objects.UserProfile = self.get_user_info(uId)
        headers.sid = self.sid


    def login(self, email: str, password: str):
        """
        Login into an account.
        **Parameters**
            - **email** : Email of the account.
            - **password** : Password of the account.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = json.dumps({
            "email": email,
            "v": 2,
            "secret": f"0 {password}",
            "deviceID": self.device_id,
            "clientType": 100,
            "action": "normal",
            "timestamp": int(timestamp() * 1000)
        })

        response = requests.post(f"{self.apip}/g/s/auth/login", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else:
            self.authenticated = True
            self.json = json.loads(response.text)
            try:
                self.sid = self.json["sid"]
            except:
                print(self.json)
            self.userId = self.json["account"]["uid"]
            self.account: objects.UserProfile = objects.UserProfile(self.json["account"]).UserProfile
            self.profile: objects.UserProfile = objects.UserProfile(self.json["userProfile"]).UserProfile
            headers.sid = 'sid='+self.sid
            return response.status_code

    def handle_socket_message(self, data):
        return self.resolve(data)

    def get_eventlog(self):
        response = requests.get(f"{self.api}/g/s/eventlog/profile?language=en", headers=headers.Headers().headers, proxies=self.proxies, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return json.loads(response.text)

    def get_from_code(self, code: str):
        """
        Get the Object Information from the Amino URL Code.

        **Parameters**
            - **code** : Code from the Amino URL.
                - ``http://aminoapps.com/p/EXAMPLE``, the ``code`` is 'EXAMPLE'.

        **Returns**
            - **Success** : :meth:`From Code Object <amino.lib.util.objects.FromCode>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.api}/g/s/link-resolution?q={code}", headers=headers.Headers().headers, proxies=self.proxies, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.FromCode(json.loads(response.text)["linkInfoV2"]).FromCode

    def join_community(self, comId: str, invitationId: str = None):
        url = f"{self.apip}/x{comId}/s/community/join"
        response = requests.post(url=url, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0:
            return exceptions.CheckException(json.loads(response.text))
        else:
            return response.status_code

    def leave_community(self, comId: str):
        url = f"{self.apip}/x{comId}/s/community/leave"
        response = requests.post(url=url, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0:
            return exceptions.CheckException(json.loads(response.text))
        else:
            return response.status_code
    def get_user_info(self, userId: str):
        url = f"{self.api}/g/s/user-profile/{userId}"
        response = requests.get(url=url, headers=headers.Headers().headers, proxies=self.proxies, verify=self.certificatePath)
        if response.status_code != 200:
            return exceptions.CheckException(json.loads(response.text))
        else:
            return objects.UserProfile(json.loads(response.text)["userProfile"]).UserProfile
    def get_from_deviceid(self, deviceId: str):
        """
        Get the User ID from an Device ID.
        **Parameters**
            - **deviceID** : ID of the Device.
        **Returns**
            - **Success** : :meth:`User ID <aminofix.lib.util.objects.UserProfile.userId>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/auid?deviceId={deviceId}")
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return json.loads(response.text)["auid"]

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
        response = requests.post(f"{self.apip}/x{self.comId}/s/chat/thread/{chatId}/message", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return response.status_code
    def get_chat_threads(self, start: int = 0, size: int = 25):
        response = requests.get(f"{self.apip}/g/s/chat/thread?type=joined-me&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.ThreadList(json.loads(response.text)["threadList"]).ThreadList

    def comment(self, message: str, userId: str = None, blogId: str = None, wikiId: str = None, replyTo: str = None):
        """
        Comment on a User's Wall, Blog or Wiki.
        **Parameters**
            - **message** : Message to be sent.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
            - **replyTo** : ID of the Comment to Reply to.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
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
            response = requests.post(f"{self.apip}/g/s/user-profile/{userId}/g-comment", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        elif blogId:
            data["eventSource"] = "PostDetailView"
            data = json.dumps(data)
            response = requests.post(f"{self.apip}/g/s/blog/{blogId}/g-comment", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = json.dumps(data)
            response = requests.post(f"{self.apip}/g/s/item/{wikiId}/g-comment", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        else: raise exceptions.SpecifyType
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        """
        Delete a Comment on a User's Wall, Blog or Wiki.
        **Parameters**
            - **commentId** : ID of the Comment.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if userId: response = requests.delete(f"{self.apip}/g/s/user-profile/{userId}/g-comment/{commentId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        elif blogId: response = requests.delete(f"{self.apip}/g/s/blog/{blogId}/g-comment/{commentId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        elif wikiId: response = requests.delete(f"{self.apip}/g/s/item/{wikiId}/g-comment/{commentId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        else: raise exceptions.SpecifyType

        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None):
        if pageToken is not None: url = f"{self.apip}/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&pageToken={pageToken}&size={size}"
        else: url = f"{self.apip}/g/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"
        response = requests.get(url, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.GetMessages(json.loads(response.text)).GetMessages
    def get_message_info(self, chatId: str, messageId: str):
        response = requests.get(f"{self.apip}/g/s/chat/thread/{chatId}/message/{messageId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.Message(json.loads(response.text)["message"]).Message

    def get_notifications(self, start: int = 0, size: int = 25):
        response = requests.get(f"{self.apip}/x{self.comId}/s/notification?pagingType=t&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.NotificationList(json.loads(response.text)["notificationList"]).NotificationList

    def sub_clients(self, start: int = 0, size: int = 25):
        response = requests.get(f"{self.apip}/g/s/community/joined?v=1&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.CommunityList(json.loads(response.text)["communityList"]).CommunityList
    def get_community_info(self, comId: str):
        response = requests.get(f"{self.apip}/g/s-x{comId}/community/info?withInfluencerList=1&withTopicList=true&influencerListOrderStrategy=fansCount", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.Community(json.loads(response.text)["community"]).Community

    def get_chat_thread(self, chatId: str):
        """
        Get the Chat Object from an Chat ID.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : :meth:`Chat Object <aminofix.lib.util.objects.Thread>`

            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/x{self.comId}/s/chat/thread/{chatId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.Thread(json.loads(response.text)["thread"]).Thread
    def get_public_chat_threads(self, type: str = "recommended", start: int = 0, size: int = 25):
        """
        List of Public Chats of the Community.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Chat List <amino.lib.util.objects.ThreadList>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/x{self.comId}/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.ThreadList(json.loads(response.text)["threadList"]).ThreadList
    def get_all_users(self, start: int = 0, size: int = 25):
        """
        Get list of users of Amino.
        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.
        **Returns**
            - **Success** : :meth:`User Profile Count List Object <aminofix.lib.util.objects.UserProfileCountList>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/user-profile?type=recent&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfileCountList(json.loads(response.text)).UserProfileCountList

    def request_verify_code(self, email: str, resetPassword: bool = False):
        data = json.dumps({
            "identity": email,
            "type": 1,
            "deviceID": self.device_id
        })

        if resetPassword is True:
            data["level"] = 2
            data["purpose"] = "reset-password"
        response = requests.post(f"{self.apip}/g/s/auth/request-security-validation", headers=headers.Headers().s_headers, proxies=self.proxies, data=data)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code
    def get_wall_comments(self, userId: str, sorting: str, start: int = 0, size: int = 25):
        """
        List of Wall Comments of an User.


        **Parameters**
            - **userId** : ID of the User.
            - **sorting** : Order of the Comments.
                - ``newest``, ``oldest``, ``top``
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Comments List <aminofix.lib.util.objects.CommentList>`

            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if sorting.lower() == "newest": sorting = "newest"
        elif sorting.lower() == "oldest": sorting = "oldest"
        elif sorting.lower() == "top": sorting = "vote"
        else: raise exceptions.WrongType(sorting)

        response = requests.get(f"{self.apip}/g/s/user-profile/{userId}/g-comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.CommentList(json.loads(response.text)["commentList"]).CommentList

    def get_blog_comments(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, sorting: str = "newest", start: int = 0, size: int = 25):
        if sorting == "newest": sorting = "newest"
        elif sorting == "oldest": sorting = "oldest"
        elif sorting == "top": sorting = "vote"
        else: raise exceptions.WrongType(sorting)

        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = requests.get(f"{self.apip}/g/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        elif wikiId: response = requests.get(f"{self.apip}/g/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        elif fileId: response = requests.get(f"{self.apip}/g/s/shared-folder/files/{fileId}/comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        else: raise exceptions.SpecifyType()

        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.CommentList(json.loads(response.text)["commentList"]).CommentList

    def get_blog_info(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None):
        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = requests.get(f"{self.apip}/g/s/blog/{blogId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
            if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
            else: return objects.GetBlogInfo(json.loads(response.text)).GetBlogInfo

        elif wikiId:
            response = requests.get(f"{self.apip}/g/s/item/{wikiId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
            if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
            else: return objects.GetWikiInfo(json.loads(response.text)).GetWikiInfo

        elif fileId:
            response = requests.get(f"{self.apip}/g/s/shared-folder/files/{fileId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
            if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
            else: return objects.SharedFolderFile(json.loads(response.text)["file"]).SharedFolderFile

        else: raise exceptions.SpecifyType()

    def get_wallet_info(self):
        """
        Get Information about the account's Wallet.

        **Parameters**
            - No parameters required.

        **Returns**
            - **Success** : :meth:`Wallet Object <aminofix.lib.util.objects.WalletInfo>`

            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.api}/g/s/wallet", headers=headers.Headers().headers, proxies=self.proxies, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.WalletInfo(json.loads(response.text)["wallet"]).WalletInfo

    def get_wallet_history(self, start: int = 0, size: int = 25):
        """
        Get the Wallet's History Information.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Wallet Object <aminofix.lib.util.objects.WalletInfo>`

            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.api}/g/s/wallet/coin/history?start={start}&size={size}", headers=headers.Headers().headers, proxies=self.proxies, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.WalletHistory(json.loads(response.text)["coinHistoryList"]).WalletHistory

    def get_blocked_users(self, start: int = 0, size: int = 25):
        """
        List of Users that the User Blocked.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Users List <aminofix.lib.util.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/block?start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfileList(json.loads(response.text)["userProfileList"]).UserProfileList
    # By Marshall (Smile, Texaz) (from SAmino)
    def watch_ad(self, uid: str = None):
        if uid: self.ad_data["reward"]["custom_json"]["hashed_user_id"] = uid
        if not uid: self.ad_data["reward"]["custom_json"]["hashed_user_id"] = self.uid
        self.ad_data["reward"]["event_id"] = str(uuid4())
        req = requests.post("https://ads.tapdaq.com/v4/analytics/reward", headers=self.ad_headers, json=self.ad_data, proxies=self.proxies)
        return req.status_code

    def upload_media(self, file: BinaryIO, fileType: str):
        """
        Upload file to the amino servers.
        **Parameters**
            - **file** : File to be uploaded.
        **Returns**
            - **Success** : Url of the file uploaded to the server.
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        if fileType == "audio":
            t = "audio/aac"
        elif fileType == "image":
            t = "image/jpg"
        else: raise exceptions.SpecifyType(fileType)

        data = file.read()
        response = requests.post(f"{self.api}/g/s/media/upload", data=data, headers=headers.Headers(type=t, data=data, deviceId=self.device_id).headers, proxies=self.proxies, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return json.loads(response.text)["mediaValue"]

    def get_from_id(self, objectId: str, objectType: int, comId: str = None):
        """
        Get the Object Information from the Object ID and Type.
        **Parameters**
            - **objectID** : ID of the Object. User ID, Blog ID, etc.
            - **objectType** : Type of the Object.
            - *comId* : ID of the Community. Use if the Object is in a Community.
        **Returns**
            - **Success** : :meth:`From Code Object <amino.lib.util.objects.FromCode>`
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = json.dumps({
            "objectId": objectId,
            "targetCode": 1,
            "objectType": objectType,
            "timestamp": int(timestamp() * 1000)
        })

        if comId: response = requests.post(f"{self.apip}/g/s-x{comId}/link-resolution", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        else: response = requests.post(f"{self.apip}/g/s/link-resolution", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.FromCode(json.loads(response.text)["linkInfoV2"]).FromCode
    def register(self, nickname: str, email: str, password: str, verificationCode: str, deviceId: str = device.device_id):
        """
        Register an account.
        **Parameters**
            - **nickname** : Nickname of the account.
            - **email** : Email of the account.
            - **password** : Password of the account.
            - **verificationCode** : Verification code.
            - **deviceId** : The device id being registered to.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """

        data = json.dumps({
            "secret": f"0 {password}",
            "deviceID": deviceId,
            "email": email,
            "clientType": 100,
            "nickname": nickname,
            "latitude": 0,
            "longitude": 0,
            "address": None,
            "clientCallbackURL": "narviiapp://relogin",
            "validationContext": {
                "data": {
                    "code": verificationCode
                },
                "type": 1,
                "identity": email
            },
            "type": 1,
            "identity": email,
            "timestamp": int(timestamp() * 1000)
        })

        response = requests.post(f"{self.apip}/g/s/auth/register", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def restore(self, email: str, password: str):
        """
        Restore a deleted account.
        **Parameters**
            - **email** : Email of the account.
            - **password** : Password of the account.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = json.dumps({
            "secret": f"0 {password}",
            "deviceID": device.device_id,
            "email": email,
            "timestamp": int(timestamp() * 1000)
        })

        response = requests.post(f"{self.apip}/g/s/account/delete-request/cancel", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code
    def logout(self):
        """
        Logout from an account.
        **Parameters**
            - No parameters required.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = json.dumps({
            "deviceID": self.device_id,
            "clientType": 100,
            "timestamp": int(timestamp() * 1000)
        })

        response = requests.post(f"{self.apip}/g/s/auth/logout", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else:
            self.authenticated = False
            self.json = None
            self.sid = None
            self.userId = None
            self.account: None
            self.profile: None
            headers.sid = None
            self.close()
            return response.status_code

    def activate_account(self, email: str, code: str):
        """
        Activate an account.
        **Parameters**
            - **email** : Email of the account.
            - **code** : Verification code.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """

        data = json.dumps({
            "type": 1,
            "identity": email,
            "data": {"code": code},
            "deviceID": device.device_id
        })

        response = requests.post(f"{self.apip}/g/s/auth/activate-email", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def delete_account(self, password: str):
        """
        Delete an account.
        **Parameters**
            - **password** : Password of the account.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """

        data = json.dumps({
            "deviceID": device.device_id,
            "secret": f"0 {password}"
        })

        response = requests.post(f"{self.api}/g/s/account/delete-request", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def change_password(self, email: str, password: str, code: str):
        """
        Change password of an account.
        **Parameters**
            - **email** : Email of the account.
            - **password** : Password of the account.
            - **code** : Verification code.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """

        data = json.dumps({
            "updateSecret": f"0 {password}",
            "emailValidationContext": {
                "data": {
                    "code": code
                },
                "type": 1,
                "identity": email,
                "level": 2,
                "deviceID": device.device_id
            },
            "phoneNumberValidationContext": None,
            "deviceID": device.device_id
        })

        response = requests.post(f"{self.apip}/g/s/auth/reset-password", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def check_device(self, deviceId: str):
        """
        Check if the Device ID is valid.
        **Parameters**
            - **deviceId** : ID of the Device.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = json.dumps({
            "deviceID": deviceId,
            "bundleID": "com.narvii.amino.master",
            "clientType": 100,
            "timezone": -timezone // 1000,
            "systemPushEnabled": True,
            "locale": locale()[0],
            "timestamp": int(timestamp() * 1000)
        })

        response = requests.post(f"{self.apip}/g/s/device", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: self.configured = True; return response.status_code

    def get_account_info(self):
        response = requests.get(f"{self.apip}/g/s/account", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfile(json.loads(response.text)["account"]).UserProfile

    def sub_clients_profile(self, start: int = 0, size: int = 25):
        if not self.authenticated: raise exceptions.NotLoggedIn()
        response = requests.get(f"{self.apip}/g/s/community/joined?v=1&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return json.loads(response.text)["userInfoInCommunities"]

    def get_chat_users(self, chatId: str, start: int = 0, size: int = 25):
        response = requests.get(f"{self.apip}/g/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfileList(json.loads(response.text)["memberList"]).UserProfileList

    def join_chat(self, chatId: str):
        """
        Join an Chat.
        **Parameters**
            - **chatId** : ID of the Chat.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/member/{self.userId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def leave_chat(self, chatId: str):
        """
        Leave an Chat.
        **Parameters**
            - **chatId** : ID of the Chat.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.delete(f"{self.apip}/g/s/chat/thread/{chatId}/member/{self.userId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def start_chat(self, userId: [str, list], message: str, title: str = None, content: str = None, isGlobal: bool = False, publishToGlobal: bool = False):
        """
        Start an Chat with an User or List of Users.
        **Parameters**
            - **userId** : ID of the User or List of User IDs.
            - **message** : Starting Message.
            - **title** : Title of Group Chat.
            - **content** : Content of Group Chat.
            - **isGlobal** : If Group Chat is Global.
            - **publishToGlobal** : If Group Chat should show in Global.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise exceptions.WrongType()

        data = {
            "title": title,
            "inviteeUids": userIds,
            "initialMessageContent": message,
            "content": content,
            "timestamp": int(timestamp() * 1000)
        }

        if isGlobal is True: data["type"] = 2; data["eventSource"] = "GlobalComposeMenu"
        else: data["type"] = 0

        if publishToGlobal is True: data["publishToGlobal"] = 1
        else: data["publishToGlobal"] = 0

        data = json.dumps(data)

        response = requests.post(f"{self.apip}/g/s/chat/thread", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def invite_to_chat(self, userId: [str, list], chatId: str):
        """
        Invite a User or List of Users to a Chat.
        **Parameters**
            - **userId** : ID of the User or List of User IDs.
            - **chatId** : ID of the Chat.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise exceptions.WrongType

        data = json.dumps({
            "uids": userIds,
            "timestamp": int(timestamp() * 1000)
        })

        response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/member/invite", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def kick(self, userId: str, chatId: str, allowRejoin: bool = True):
        if allowRejoin: allowRejoin = 1
        if not allowRejoin: allowRejoin = 0
        response = requests.delete(f"{self.apip}/g/s/chat/thread/{chatId}/member/{userId}?allowRejoin={allowRejoin}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def search_community(self, aminoId: str):
        """
        Search a Community byt its Amino ID.
        **Parameters**
            - **aminoId** : Amino ID of the Community.
        **Returns**
            - **Success** : :meth:`Community List <aminofix.lib.util.objects.CommunityList>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/search/amino-id-and-link?q={aminoId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else:
            response = json.loads(response.text)["resultList"]
            if len(response) == 0: raise exceptions.CommunityNotFound(aminoId)
            else: return objects.CommunityList([com["refObject"] for com in response]).CommunityList

    def get_user_following(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that the User is Following.
        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.
        **Returns**
            - **Success** : :meth:`User List <aminofix.lib.util.objects.UserProfileList>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/user-profile/{userId}/joined?start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfileList(json.loads(response.text)["userProfileList"]).UserProfileList

    def get_user_followers(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that are Following the User.
        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.
        **Returns**
            - **Success** : :meth:`User List <amino.lib.util.objects.UserProfileList>`
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/user-profile/{userId}/member?start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfileList(json.loads(response.text)["userProfileList"]).UserProfileList

    def get_user_visitors(self, userId: str, start: int = 0, size: int = 25):
        """
        List of Users that Visited the User.
        **Parameters**
            - **userId** : ID of the User.
            - *start* : Where to start the list.
            - *size* : Size of the list.
        **Returns**
            - **Success** : :meth:`Visitors List <amino.lib.util.objects.VisitorsList>`
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/user-profile/{userId}/visitors?start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.VisitorsList(json.loads(response.text)).VisitorsList

    def get_blocker_users(self, start: int = 0, size: int = 25):
        """
        List of Users that are Blocking the User.
        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.
        **Returns**
            - **Success** : :meth:`List of User IDs <None>`
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/block/full-list?start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return json.loads(response.text)["blockerUidList"]

    def flag(self, reason: str, flagType: int, userId: str = None, blogId: str = None, wikiId: str = None, asGuest: bool = False):
        """
        Flag a User, Blog or Wiki.
        **Parameters**
            - **reason** : Reason of the Flag.
            - **flagType** : Type of the Flag.
            - **userId** : ID of the User.
            - **blogId** : ID of the Blog.
            - **wikiId** : ID of the Wiki.
            - *asGuest* : Execute as a Guest.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        if reason is None: raise exceptions.ReasonNeeded
        if flagType is None: raise exceptions.FlagTypeNeeded

        data = {
            "flagType": flagType,
            "message": reason,
            "timestamp": int(timestamp() * 1000)
        }

        if userId:
            data["objectId"] = userId
            data["objectType"] = 0

        elif blogId:
            data["objectId"] = blogId
            data["objectType"] = 1

        elif wikiId:
            data["objectId"] = wikiId
            data["objectType"] = 2

        else: raise exceptions.SpecifyType

        if asGuest: flg = "g-flag"
        else: flg = "flag"

        data = json.dumps(data)
        response = requests.post(f"{self.apip}/g/s/{flg}", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def mark_as_read(self, chatId: str, messageId: str):
        """
        Mark a Message from a Chat as Read.
        **Parameters**
            - **messageId** : ID of the Message.
            - **chatId** : ID of the Chat.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = json.dumps({
            "messageId": messageId,
            "timestamp": int(timestamp() * 1000)
        })
        response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/mark-as-read", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def edit_chat(self, chatId: str, doNotDisturb: bool = None, pinChat: bool = None, title: str = None, icon: str = None, backgroundImage: str = None, content: str = None, announcement: str = None, coHosts: list = None, keywords: list = None, pinAnnouncement: bool = None, publishToGlobal: bool = None, canTip: bool = None, viewOnly: bool = None, canInvite: bool = None, fansOnly: bool = None):
        """
        Send a Message to a Chat.
        **Parameters**
            - **chatId** : ID of the Chat.
            - **title** : Title of the Chat.
            - **content** : Content of the Chat.
            - **icon** : Icon of the Chat.
            - **backgroundImage** : Url of the Background Image of the Chat.
            - **announcement** : Announcement of the Chat.
            - **pinAnnouncement** : If the Chat Announcement should Pinned or not.
            - **coHosts** : List of User IDS to be Co-Host.
            - **keywords** : List of Keywords of the Chat.
            - **viewOnly** : If the Chat should be on View Only or not.
            - **canTip** : If the Chat should be Tippable or not.
            - **canInvite** : If the Chat should be Invitable or not.
            - **fansOnly** : If the Chat should be Fans Only or not.
            - **publishToGlobal** : If the Chat should show on Public Chats or not.
            - **doNotDisturb** : If the Chat should Do Not Disturb or not.
            - **pinChat** : If the Chat should Pinned or not.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        data = {"timestamp": int(timestamp() * 1000)}

        if title: data["title"] = title
        if content: data["content"] = content
        if icon: data["icon"] = icon
        if keywords: data["keywords"] = keywords
        if announcement: data["extensions"] = {"announcement": announcement}
        if pinAnnouncement: data["extensions"] = {"pinAnnouncement": pinAnnouncement}
        if fansOnly: data["extensions"] = {"fansOnly": fansOnly}

        if publishToGlobal: data["publishToGlobal"] = 0
        if not publishToGlobal: data["publishToGlobal"] = 1

        res = []

        if doNotDisturb is not None:
            if doNotDisturb:
                data = json.dumps({"alertOption": 2, "timestamp": int(timestamp() * 1000)})
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/member/{self.userId}/alert", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

            if not doNotDisturb:
                data = json.dumps({"alertOption": 1, "timestamp": int(timestamp() * 1000)})
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/member/{self.userId}/alert", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

        if pinChat is not None:
            if pinChat:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/pin", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

            if not pinChat:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/unpin", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

        if backgroundImage is not None:
            data = json.dumps({"media": [100, backgroundImage, None], "timestamp": int(timestamp() * 1000)})
            response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/member/{self.userId}/background", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
            if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
            else: res.append(response.status_code)

        if coHosts is not None:
            data = json.dumps({"uidList": coHosts, "timestamp": int(timestamp() * 1000)})
            response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/co-host", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
            if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
            else: res.append(response.status_code)

        if viewOnly is not None:
            if viewOnly:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/view-only/enable", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

            if not viewOnly:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/view-only/disable", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

        if canInvite is not None:
            if canInvite:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/members-can-invite/enable", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

            if not canInvite:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/members-can-invite/disable", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

        if canTip is not None:
            if canTip:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/tipping-perm-status/enable", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

            if not canTip:
                response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/tipping-perm-status/disable", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
                if json.loads(response.text)["api:statuscode"] != 0: res.append(exceptions.CheckException(json.loads(response.text)))
                else: res.append(response.status_code)

        data = json.dumps(data)
        response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if response.status_code != 200: res.append(exceptions.CheckException(json.loads(response.text)))
        else: res.append(response.status_code)

        return res

    def visit(self, userId: str):
        """
        Visit an User.
        **Parameters**
            - **userId** : ID of the User.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/user-profile/{userId}?action=visit", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def send_coins(self, coins: int, blogId: str = None, chatId: str = None, objectId: str = None, transactionId: str = None):
        url = None
        if transactionId is None: transactionId = str(UUID(hexlify(urandom(16)).decode('ascii')))

        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": int(timestamp() * 1000)
        }

        if blogId is not None: url = f"{self.apip}/g/s/blog/{blogId}/tipping"
        if chatId is not None: url = f"{self.apip}/g/s/chat/thread/{chatId}/tipping"
        if objectId is not None:
            data["objectId"] = objectId
            data["objectType"] = 2
            url = f"{self.api}/g/s/tipping"

        if url is None: raise exceptions.SpecifyType()

        data = json.dumps(data)
        response = requests.post(url, headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def follow(self, userId: [str, list]):
        """
        Follow an User or Multiple Users.
        **Parameters**
            - **userId** : ID of the User or List of IDs of the Users.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if isinstance(userId, str):
            response = requests.post(f"{self.apip}/g/s/user-profile/{userId}/member", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)

        elif isinstance(userId, list):
            data = json.dumps({"targetUidList": userId, "timestamp": int(timestamp() * 1000)})
            response = requests.post(f"{self.apip}/g/s/user-profile/{self.userId}/joined", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        else: raise exceptions.WrongType

        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def unfollow(self, userId: str):
        """
        Unfollow an User.
        **Parameters**
            - **userId** : ID of the User.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.delete(f"{self.apip}/g/s/user-profile/{userId}/member/{self.userId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def block(self, userId: str):
        """
        Block an User.
        **Parameters**
            - **userId** : ID of the User.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.post(f"{self.apip}/g/s/block/{userId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def unblock(self, userId: str):
        """
        Unblock an User.
        **Parameters**
            - **userId** : ID of the User.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.delete(f"{self.apip}/g/s/block/{userId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def request_join_community(self, comId: str, message: str = None):
        """
        Request to join a Community.
        **Parameters**
            - **comId** : ID of the Community.
            - **message** : Message to be sent.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        data = json.dumps({"message": message, "timestamp": int(timestamp() * 1000)})
        response = requests.post(f"{self.apip}/x{comId}/s/community/membership-request", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def flag_community(self, comId: str, reason: str, flagType: int, isGuest: bool = False):
        """
        Flag a Community.
        **Parameters**
            - **comId** : ID of the Community.
            - **reason** : Reason of the Flag.
            - **flagType** : Type of Flag.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if reason is None: raise exceptions.ReasonNeeded
        if flagType is None: raise exceptions.FlagTypeNeeded

        data = json.dumps({
            "objectId": comId,
            "objectType": 16,
            "flagType": flagType,
            "message": reason,
            "timestamp": int(timestamp() * 1000)
        })

        if isGuest: flg = "g-flag"
        else: flg = "flag"

        response = requests.post(f"{self.apip}/x{comId}/s/{flg}", data=data, headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def edit_profile(self, nickname: str = None, content: str = None, icon: BinaryIO = None, backgroundColor: str = None, backgroundImage: str = None, defaultBubbleId: str = None):
        """
        Edit account's Profile.
        **Parameters**
            - **nickname** : Nickname of the Profile.
            - **content** : Biography of the Profile.
            - **icon** : Icon of the Profile.
            - **backgroundImage** : Url of the Background Picture of the Profile.
            - **backgroundColor** : Hexadecimal Background Color of the Profile.
            - **defaultBubbleId** : Chat bubble ID.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        data = {
            "address": None,
            "latitude": 0,
            "longitude": 0,
            "mediaList": None,
            "eventSource": "UserProfileView",
            "timestamp": int(timestamp() * 1000)
        }

        if nickname: data["nickname"] = nickname
        if icon: data["icon"] = self.upload_media(icon, "image")
        if content: data["content"] = content
        if backgroundColor: data["extensions"] = {"style": {"backgroundColor": backgroundColor}}
        if backgroundImage: data["extensions"] = {"style": {"backgroundMediaList": [[100, backgroundImage, None, None, None]]}}
        if defaultBubbleId: data["extensions"] = {"defaultBubbleId": defaultBubbleId}

        data = json.dumps(data)
        response = requests.post(f"{self.apip}/g/s/user-profile/{self.userId}", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def set_privacy_status(self, isAnonymous: bool = False, getNotifications: bool = False):
        """
        Edit account's Privacy Status.
        **Parameters**
            - **isAnonymous** : If visibility should be Anonymous or not.
            - **getNotifications** : If account should get new Visitors Notifications.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """

        data = {"timestamp": int(timestamp() * 1000)}

        if not isAnonymous: data["privacyMode"] = 1
        if isAnonymous: data["privacyMode"] = 2
        if not getNotifications: data["notificationStatus"] = 2
        if getNotifications: data["privacyMode"] = 1

        data = json.dumps(data)
        response = requests.post(f"{self.apip}/g/s/account/visit-settings", headers=sheaders.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def set_amino_id(self, aminoId: str):
        """
        Edit account's Amino ID.
        **Parameters**
            - **aminoId** : Amino ID of the Account.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        data = json.dumps({"aminoId": aminoId, "timestamp": int(timestamp() * 1000)})
        response = requests.post(f"{self.api}/g/s/account/change-amino-id", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_linked_communities(self, userId: str):
        """
        Get a List of Linked Communities of an User.
        **Parameters**
            - **userId** : ID of the User.
        **Returns**
            - **Success** : :meth:`Community List <aminofix.lib.util.objects.CommunityList>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/user-profile/{userId}/linked-community", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.CommunityList(json.loads(response.text)["linkedCommunityList"]).CommunityList

    def get_unlinked_communities(self, userId: str):
        """
        Get a List of Unlinked Communities of an User.
        **Parameters**
            - **userId** : ID of the User.
        **Returns**
            - **Success** : :meth:`Community List <aminofix.lib.util.objects.CommunityList>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/user-profile/{userId}/linked-community", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.CommunityList(json.loads(response.text)["unlinkedCommunityList"]).CommunityList

    def reorder_linked_communities(self, comIds: list):
        """
        Reorder List of Linked Communities.
        **Parameters**
            - **comIds** : IDS of the Communities.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = json.dumps({"ndcIds": comIds, "timestamp": int(timestamp() * 1000)})
        response = requests.post(f"{self.apip}/g/s/user-profile/{self.userId}/linked-community/reorder", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def add_linked_community(self, comId: str):
        """
        Add a Linked Community on your profile.
        **Parameters**
            - **comId** : ID of the Community.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.post(f"{self.apip}/g/s/user-profile/{self.userId}/linked-community/{comId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def remove_linked_community(self, comId: str):
        """
        Remove a Linked Community on your profile.
        **Parameters**
            - **comId** : ID of the Community.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.delete(f"{self.apip}/g/s/user-profile/{self.userId}/linked-community/{comId}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def like_blog(self, blogId: [str, list] = None, wikiId: str = None):
        """
        Like a Blog, Multiple Blogs or a Wiki.
        **Parameters**
            - **blogId** : ID of the Blog or List of IDs of the Blogs. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        data = {
            "value": 4,
            "timestamp": int(timestamp() * 1000)
        }

        if blogId:
            if isinstance(blogId, str):
                data["eventSource"] = "UserProfileView"
                data = json.dumps(data)
                response = requests.post(f"{self.apip}/g/s/blog/{blogId}/g-vote?cv=1.2", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

            elif isinstance(blogId, list):
                data["targetIdList"] = blogId
                data = json.dumps(data)
                response = requests.post(f"{self.apip}/g/s/feed/g-vote", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

            else: raise exceptions.WrongType(type(blogId))

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = json.dumps(data)
            response = requests.post(f"{self.api}/g/s/item/{wikiId}/g-vote?cv=1.2", headers=self.parse_headers(data=data), data=data, proxies=self.proxies, verify=self.certificatePath)

        else: raise exceptions.SpecifyType()

        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def unlike_blog(self, blogId: str = None, wikiId: str = None):
        """
        Remove a like from a Blog or Wiki.
        **Parameters**
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if blogId: response = requests.delete(f"{self.apip}/g/s/blog/{blogId}/g-vote?eventSource=UserProfileView", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        elif wikiId: response = requests.delete(f"{self.apip}/g/s/item/{wikiId}/g-vote?eventSource=PostDetailView", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        else: raise exceptions.SpecifyType

        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def like_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        """
        Like a Comment on a User's Wall, Blog or Wiki.
        **Parameters**
            - **commentId** : ID of the Comment.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        data = {
            "value": 4,
            "timestamp": int(timestamp() * 1000)
        }

        if userId:
            data["eventSource"] = "UserProfileView"
            data = json.dumps(data)
            response = requests.post(f"{self.apip}/g/s/user-profile/{userId}/comment/{commentId}/g-vote?cv=1.2&value=1", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        elif blogId:
            data["eventSource"] = "PostDetailView"
            data = json.dumps(data)
            response = requests.post(f"{self.apip}/g/s/blog/{blogId}/comment/{commentId}/g-vote?cv=1.2&value=1", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        elif wikiId:
            data["eventSource"] = "PostDetailView"
            data = json.dumps(data)
            response = requests.post(f"{self.apip}/g/s/item/{wikiId}/comment/{commentId}/g-vote?cv=1.2&value=1", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)

        else: raise exceptions.SpecifyType

        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def unlike_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        """
        Remove a like from a Comment on a User's Wall, Blog or Wiki.
        **Parameters**
            - **commentId** : ID of the Comment.
            - **userId** : ID of the User. (for Walls)
            - **blogId** : ID of the Blog. (for Blogs)
            - **wikiId** : ID of the Wiki. (for Wikis)
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if userId: response = requests.delete(f"{self.apip}/g/s/user-profile/{userId}/comment/{commentId}/g-vote?eventSource=UserProfileView", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        elif blogId: response = requests.delete(f"{self.apip}/g/s/blog/{blogId}/comment/{commentId}/g-vote?eventSource=PostDetailView", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        elif wikiId: response = requests.delete(f"{self.apip}/g/s/item/{wikiId}/comment/{commentId}/g-vote?eventSource=PostDetailView", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        else: raise exceptions.SpecifyType

        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_membership_info(self):
        """
        Get Information about your Amino+ Membership.
        **Parameters**
            - No parameters required.
        **Returns**
            - **Success** : :meth:`Membership Object <aminofix.lib.util.objects.Membership>`
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/membership?force=true", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.Membership(json.loads(response.text)).Membership

    def get_ta_announcements(self, language: str = "en", start: int = 0, size: int = 25):
        """
        Get the list of Team Amino's Announcement Blogs.
        **Parameters**
            - **language** : Language of the Blogs.
                - ``en``, ``es``, ``pt``, ``ar``, ``ru``, ``fr``, ``de``
            - *start* : Where to start the list.
            - *size* : Size of the list.
        **Returns**
            - **Success** : :meth:`Blogs List <aminofix.lib.util.objects.BlogList>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        if language not in self.get_supported_languages(): raise exceptions.UnsupportedLanguage(language)
        response = requests.get(f"{self.apip}/g/s/announcement?language={language}&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.BlogList(json.loads(response.text)["blogList"]).BlogList

    def get_supported_languages(self):
        """
        Get the List of Supported Languages by Amino.
        **Parameters**
            - No parameters required.
        **Returns**
            - **Success** : :meth:`List of Supported Languages <List>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/community-collection/supported-languages?start=0&size=100", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return json.loads(response.text)["supportedLanguages"]

    def claim_new_user_coupon(self):
        """
        Claim the New User Coupon available when a new account is created.
        **Parameters**
            - No parameters required.
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.post(f"{self.api}/g/s/coupon/new-user-coupon/claim", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_subscriptions(self, start: int = 0, size: int = 25):
        """
        Get Information about the account's Subscriptions.
        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.
        **Returns**
            - **Success** : :meth:`List <List>`
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """
        response = requests.get(f"{self.apip}/g/s/store/subscription?objectType=122&start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return json.loads(response.text)["storeSubscriptionItemList"]

    def accept_host(self, chatId: str, requestId: str):
        data = json.dumps({})

        response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/transfer-organizer/{requestId}/accept", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def accept_organizer(self, chatId: str, requestId: str):
        self.accept_host(chatId, requestId)

    # Contributed by 'https://github.com/LynxN1'
    def link_identify(self, code: str):
        response = requests.get(f"{self.apip}/g/s/community/link-identify?q=http%3A%2F%2Faminoapps.com%2Finvite%2F{code}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        return json.loads(response.text)

    def invite_to_vc(self, chatId: str, userId: str):
        """
        Invite a User to a Voice Chat
        **Parameters**
            - **chatId** - ID of the Chat
            - **userId** - ID of the User
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """

        data = json.dumps({
            "uid": userId
        })

        response = requests.post(f"{self.apip}/g/s/chat/thread/{chatId}/vvchat-presenter/invite", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def wallet_config(self, level: int):
        """
        Changes ads config
        **Parameters**
            - **level** - Level of the ads.
                - ``1``, ``2``
        **Returns**
            - **Success** : 200 (int)
            - **Fail** : :meth:`Exceptions <aminofix.lib.util.exceptions>`
        """

        data = json.dumps({
            "adsLevel": level,
            "timestamp": int(timestamp() * 1000)
        })

        response = requests.post(f"{self.apip}/g/s/wallet/ads/config", headers=headers.Headers().s_headers, data=data, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_avatar_frames(self, start: int = 0, size: int = 25):
        response = requests.get(f"{self.apip}/g/s/avatar-frame?start={start}&size={size}", headers=headers.Headers().s_headers, proxies=self.proxies, verify=self.certificatePath)
        if json.loads(response.text)["api:statuscode"] != 0: return exceptions.CheckException(json.loads(response.text))
        else: return objects.AvatarFrameList(json.loads(response.text)["avatarFrameList"]).AvatarFrameList

#fix Amino.py 1.2.17 by Minori
#SAmino - https://github.com/SirLez/SAmino
#Amino.py - https://github.com/Slimakoi/Amino.py