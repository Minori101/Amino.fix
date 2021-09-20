import hmac
import json
import base64
import requests
import time
from hashlib import sha1
import os

from uuid import UUID
from os import urandom
from hashlib import sha1
from time import timezone
from typing import BinaryIO
from binascii import hexlify
from time import time as timestamp
from json_minify import json_minify

from . import client
from .lib.util import exceptions, device, objects, headers

def gen_msg_sig():
    return base64.b64encode(bytes.fromhex("22") + hmac.new(bytes.fromhex(str(int(time.time()))), "22".encode("utf-8"),
                                                           sha1).digest()).decode()

device = device.DeviceGenerator()

class SubClient(client.Client):
    def __init__(self, comId: str = None, sid: str = None, aminoId: str = None, *, profile: objects.UserProfile = None):
        client.Client.__init__(self)
        self.vc_connect = False

        if comId is not None:
            self.comId = comId
            self.community: objects.Community = self.get_community_info(comId)

        if aminoId is not None:
            self.comId = client.Client().search_community(aminoId).comId[0]
            self.community: objects.Community = client.Client().get_community_info(self.comId)

        if comId is None and aminoId is None: raise exceptions.NoCommunity()

        try: self.profile: objects.UserProfile = self.get_user_info(userId=profile.userId)
        except AttributeError: raise exceptions.FailedLogin()
        except exceptions.UserUnavailable: pass
    def get_online_users(self, start: int = 0, size: int = 25):
        headers.sig = gen_msg_sig()
        response = requests.get(f"{self.api}/x{self.comId}/s/live-layer?topic=ndtopic:x{self.comId}:online-members&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.UserProfileCountList(json.loads(response.text)).UserProfileCountList

    def user_active_time(self):
        data = {"ndcId": self.comId}
        response = requests.post("https://aminoapps.com/api/community/stats/web-user-active-time", json=data, headers=headers.Headers().web_headers)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_chat_users(self, chatId: str, start: int = 0, size: int = 25):
        response = requests.get(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/member?start={start}&size={size}&type=default&cv=1.2", headers=headers.Headers().s_headers, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.UserProfileList(json.loads(response.text)["memberList"]).UserProfileList

    def delete_message(self, chatId: str, messageId: str, asStaff: bool = False, reason: str = None):
        """
        Delete a Message from a Chat.

        **Parameters**
            - **messageId** : ID of the Message.
            - **chatId** : ID of the Chat.
            - **asStaff** : If execute as a Staff member (Leader or Curator).
            - **reason** : Reason of the action to show on the Moderation History.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        data = {
            "adminOpName": 102,
            "timestamp": int(timestamp() * 1000)
        }
        if asStaff and reason:
            data["adminOpNote"] = {"content": reason}

        data = json.dumps(data)
        if not asStaff: response = requests.delete(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}", headers=headers.Headers().headers, verify=self.certificatePath)
        else: response = requests.post(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}/admin", headers=headers.Headers().headers, data=data, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_public_chat_threads(self, type: str = "recommended", start: int = 0, size: int = 25):
        headers.sig = gen_msg_sig()
        response = requests.get(f"{self.api}/x{self.comId}/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.ThreadList(json.loads(response.text)["threadList"]).ThreadList
    #from SAmino
    def start_chat(self, userId: [str, list], title: str = None, message: str = None, content: str = None, type: int = 0):
        if isinstance(userId, str): userIds = [userId]
        elif isinstance(userId, list): userIds = userId
        else: raise TypeError("")
        data = {
            "ndcId": self.comId,
            "inviteeUids": userIds,
            "initialMessageContent": message,
            "type": type
        }
        req = requests.post("https://aminoapps.com/api/create-chat-thread", json=data, headers=self.web_headers)
        try:
            if "OK" not in req.json()["result"]["api:message"]: return exceptions.CheckException(json.loads(req.text))
            else: return req.status_code
        except: exceptions.CheckException(json.loads(req.text))
        return req.status_code

    def get_notifications(self, start: int = 0, size: int = 25):
        headers.sig = gen_msg_sig()
        response = requests.get(f"{self.api}/x{self.comId}/s/notification?pagingType=t&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.NotificationList(json.loads(response.text)["notificationList"]).NotificationList

    def get_invite_codes(self, status: str = "normal", start: int = 0, size: int = 25):
        headers.sig = gen_msg_sig()
        response = requests.get(f"{self.api}/g/s-x{self.comId}/community/invitation?status={status}&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.InviteCodeList(json.loads(response.text)["communityInvitationList"]).InviteCodeList

    def generate_invite_code(self, duration: int = 0, force: bool = True):
        data = json.dumps({
            "duration": duration,
            "force": force,
            "timestamp": int(timestamp() * 1000)
        })
        headers.sig = gen_msg_sig()
        response = requests.post(f"{self.api}/g/s-x{self.comId}/community/invitation", headers=headers.Headers().headers, data=data, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.InviteCode(json.loads(response.text)["communityInvitation"]).InviteCode

    def get_message_info(self, chatId: str, messageId: str):
        """
        Information of an Message from an Chat.
        **Parameters**
            - **chatId** : ID of the Chat.
            - **message** : ID of the Message.
        **Returns**
            - **Success** : :meth:`Message Object <amino.lib.util.objects.Message>`
            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/message/{messageId}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.Message(json.loads(response.text)["message"]).Message

    def search_users(self, nickname: str, start: int = 0, size: int = 25):
        headers.sig = gen_msg_sig()
        response = requests.get(f"{self.api}/x{self.comId}/s/user-profile?type=name&q={nickname}&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return objects.UserProfileList(json.loads(response.text)["userProfileList"]).UserProfileList

    def kick(self, userId: str, chatId: str, allowRejoin: bool = True):
        if allowRejoin: allowRejoin = 1
        if not allowRejoin: allowRejoin = 0
        response = requests.delete(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{userId}?allowRejoin={allowRejoin}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_chat_thread(self, chatId: str):
        """
        Get the Chat Object from an Chat ID.

        **Parameters**
            - **chatId** : ID of the Chat.

        **Returns**
            - **Success** : :meth:`Chat Object <amino.lib.util.objects.Thread>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
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
        response = requests.get(f"{self.api}/x{self.comId}/s/chat/thread?type=public-all&filterType={type}&start={start}&size={size}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.ThreadList(json.loads(response.text)["threadList"]).ThreadList

    def get_all_users(self, type: str = "recent", start: int = 0, size: int = 25):
        if type == "recent": response = requests.get(f"{self.api}/x{self.comId}/s/user-profile?type=recent&start={start}&size={size}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        elif type == "banned": response = requests.get(f"{self.api}/x{self.comId}/s/user-profile?type=banned&start={start}&size={size}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        elif type == "featured": response = requests.get(f"{self.api}/x{self.comId}/s/user-profile?type=featured&start={start}&size={size}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        elif type == "leaders": response = requests.get(f"{self.api}/x{self.comId}/s/user-profile?type=leaders&start={start}&size={size}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        elif type == "curators": response = requests.get(f"{self.api}/x{self.comId}/s/user-profile?type=curators&start={start}&size={size}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        else: raise exceptions.WrongType(type)

        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfileCountList(json.loads(response.text)).UserProfileCountList

    def join_chat(self, chatId: str):
        url = f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}"
        headers.sig = gen_msg_sig()
        response = requests.post(url=url, headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200:
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return json.loads(response.text)

    def leave_chat(self, chatId: str):
        url = f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/member/{self.userId}"
        headers.sig = gen_msg_sig()
        response = requests.delete(url=url, headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200:
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return json.loads(response.text)

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
        headers.sig = gen_msg_sig()
        response = requests.post(f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/message", headers=headers.Headers().headers, data=data, verify=self.certificatePath)
        if response.status_code != 200: 
            return exceptions.CheckException(json.loads(response.text))
        else: 
            return response.status_code
    def send_coins(self, coins: int, blogId: str = None, chatId: str = None, objectId: str = None, transactionId: str = None):
        url = None
        if transactionId is None: transactionId = str(UUID(hexlify(urandom(16)).decode('ascii')))

        data = {
            "coins": coins,
            "tippingContext": {"transactionId": transactionId},
            "timestamp": int(timestamp() * 1000)
        }

        if blogId is not None: url = f"{self.api}/x{self.comId}/s/blog/{blogId}/tipping"
        if chatId is not None: url = f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/tipping"
        if objectId is not None:
            data["objectId"] = objectId
            data["objectType"] = 2
            url = f"{self.api}/x{self.comId}/s/tipping"

        if url is None: raise exceptions.SpecifyType()

        data = json.dumps(data)
        headers.sig = gen_msg_sig()
        response = requests.post(url, headers=headers.Headers().s_headers, data=data, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code
    def get_chat_threads(self, start: int = 0, size: int = 25):
        """
        List of Chats the account is in.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Chat List <amino.lib.util.objects.ThreadList>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.api}/x{self.comId}/s/chat/thread?type=joined-me&start={start}&size={size}", headers=headers.Headers().s_headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.ThreadList(json.loads(response.text)["threadList"]).ThreadList
    def follow(self, userId: [str, list]):
        """
        Follow an User or Multiple Users.

        **Parameters**
            - **userId** : ID of the User or List of IDs of the Users.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        if isinstance(userId, str):
            headers.sig = gen_msg_sig()
            response = requests.post(f"{self.api}/x{self.comId}/s/user-profile/{userId}/member", headers=headers.Headers().headers, verify=self.certificatePath)

        elif isinstance(userId, list):
            data = json.dumps({})
            headers.sig = gen_msg_sig()
            response = requests.post(f"{self.api}/x{self.comId}/s/user-profile/{self.profile.userId}/joined", headers=headers.Headers().headers, data=data, verify=self.certificatePath)

        else: raise exceptions.WrongType(type(userId))

        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code
    def unfollow(self, userId: str):
        """
        Unfollow an User.

        **Parameters**
            - **userId** : ID of the User.

        **Returns**
            - **Success** : 200 (int)

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        headers.sig = gen_msg_sig()
        response = requests.delete(f"{self.api}/x{self.comId}/s/user-profile/{self.profile.userId}/joined/{userId}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code
    def get_chat_messages(self, chatId: str, size: int = 25, pageToken: str = None):
        """
        List of Messages from an Chat.

        **Parameters**
            - **chatId** : ID of the Chat.
            - *size* : Size of the list.
            - *pageToken* : Next Page Token.

        **Returns**
            - **Success** : :meth:`Message List <amino.lib.util.objects.MessageList>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """

        if pageToken is not None: url = f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&pageToken={pageToken}&size={size}"
        else: url = f"{self.api}/x{self.comId}/s/chat/thread/{chatId}/message?v=2&pagingType=t&size={size}"
        headers.sig = gen_msg_sig()
        response = requests.get(url, headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.GetMessages(json.loads(response.text)).GetMessages

    def get_blog_info(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None):
        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = requests.get(f"{self.api}/x{self.comId}/s/blog/{blogId}", headers=headers.Headers().headers, verify=self.certificatePath)
            if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
            else: return objects.GetBlogInfo(json.loads(response.text)).GetBlogInfo

        elif wikiId:
            response = requests.get(f"{self.api}/x{self.comId}/s/item/{wikiId}", headers=headers.Headers().headers,  verify=self.certificatePath)
            if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
            else: return objects.GetWikiInfo(json.loads(response.text)).GetWikiInfo

        elif fileId:
            response = requests.get(f"{self.api}/x{self.comId}/s/shared-folder/files/{fileId}", headers=headers.Headers().headers, verify=self.certificatePath)
            if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
            else: return objects.SharedFolderFile(json.loads(response.text)["file"]).SharedFolderFile

        else: raise exceptions.SpecifyType()

    def get_blog_comments(self, blogId: str = None, wikiId: str = None, quizId: str = None, fileId: str = None, sorting: str = "newest", start: int = 0, size: int = 25):
        if sorting == "newest": sorting = "newest"
        elif sorting == "oldest": sorting = "oldest"
        elif sorting == "top": sorting = "vote"

        if blogId or quizId:
            if quizId is not None: blogId = quizId
            response = requests.get(f"{self.api}/x{self.comId}/s/blog/{blogId}/comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        elif wikiId: response = requests.get(f"{self.api}/x{self.comId}/s/item/{wikiId}/comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        elif fileId: response = requests.get(f"{self.api}/x{self.comId}/s/shared-folder/files/{fileId}/comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        else: raise exceptions.SpecifyType()

        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.CommentList(json.loads(response.text)["commentList"]).CommentList

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
            - **Success** : :meth:`Comments List <amino.lib.util.objects.CommentList>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        if sorting == "newest": sorting = "newest"
        elif sorting == "oldest": sorting = "oldest"
        elif sorting == "top": sorting = "vote"
        else: raise exceptions.WrongType(sorting)

        response = requests.get(f"{self.api}/x{self.comId}/s/user-profile/{userId}/comment?sort={sorting}&start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.CommentList(json.loads(response.text)["commentList"]).CommentList

    def delete_blog(self, blogId: str):
        response = requests.delete(f"{self.api}/x{self.comId}/s/blog/{blogId}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def delete_wiki(self, wikiId: str):
        response = requests.delete(f"{self.api}/x{self.comId}/s/item/{wikiId}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def get_blocked_users(self, start: int = 0, size: int = 25):
        """
        List of Users that the User Blocked.

        **Parameters**
            - *start* : Where to start the list.
            - *size* : Size of the list.

        **Returns**
            - **Success** : :meth:`Users List <amino.lib.util.objects.UserProfileList>`

            - **Fail** : :meth:`Exceptions <amino.lib.util.exceptions>`
        """
        response = requests.get(f"{self.api}/x{self.comId}/s/block?start={start}&size={size}", headers=headers.Headers().headers, verify=self.certificatePath)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return objects.UserProfileList(json.loads(response.text)["userProfileList"]).UserProfileList

    def comment(self, message: str, userId: str = None, blogId: str = None, wikiId: str = None, replyTo: str = None, isGuest: bool = False):
        data = {
            "ndcId": self.comId,
            "content": message
        }
        if blogId: data["postType"] = "blog"; postId = blogId
        if wikiId: data["postType"] = "wiki"; postId = wikiId
        if userId: data["postType"] = "user"; postId = userId
        data["postId"] = postId
        response = requests.post("https://aminoapps.com/api/submit_comment", json=data, headers=self.web_headers)
        if response.status_code != 200: return exceptions.CheckException(json.loads(response.text))
        else: return response.status_code

    def delete_comment(self, commentId: str, userId: str = None, blogId: str = None, wikiId: str = None):
        if userId: response = requests.delete(f"{self.api}/x{self.comId}/s/user-profile/{userId}/comment/{commentId}", headers=headers.Headers().headers)
        if blogId: response = requests.delete(f"{self.api}/x{self.comId}/s/blog/{blogId}/comment/{commentId}", headers=headers.Headers().headers)
        if wikiId: response = requests.delete(f"{self.api}/x{self.comId}/s/item/{wikiId}/comment/{commentId}", headers=headers.Headers().headers)
        if response.status_code != 200: return CheckExceptions(response.json())
        else: return response.status_code