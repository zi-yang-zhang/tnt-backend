import requests


class User:
    def __init__(self, base):
        self.base = base
        self.endpoint = base.get_host() + '/' + 'plugins/restapi/v1/users'

    def create_user(self, user):
        return self.base.execute(requests.post, self.endpoint, json=user)


class ChatRoom:
    def __init__(self, base):
        self.base = base
        self.endpoint = base.get_host() + '/' + 'plugins/restapi/v1/chatrooms'

    def retrieve_chatroom_occupants(self, chatroom_name, service_name=""):
        self.endpoint += '/' + chatroom_name
        if service_name != "":
            payload = {'servicename': service_name}
            return self.base.execute(requests.get, self.endpoint, params=payload)
        return self.base.execute(requests.get, self.endpoint)
