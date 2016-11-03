from flask import current_app


class Api:
    User = 'User'
    ChatRoom = 'ChatRoom'
    Group = 'Group'
    System = 'System'
    Session = 'Session'


class ApiFactory:

    def __init__(self, api, host, auth):
        from endpoints import User
        base = _BaseConnection(host, auth)
        self.api = {'User': User(base)}[api]

    def get_api(self):
        return self.api


class _BaseConnection:
    def __init__(self, host, auth):
        self.headers = {'Authorization': auth, 'Accept': 'application/json', 'Content-Type': 'application/json'}
        self.host = host

    def execute(self, method, endpoint=None, **kwargs):

        current_app.logger.debug('perform request to: {}'.format(endpoint))
        current_app.logger.debug(kwargs)
        response = method(url=endpoint, headers=self.headers, **kwargs)

        current_app.logger.debug('status_code: {}'.format(str(response.status_code)))

        if response.status_code in (200, 201):
            try:
                return response.json()
            except:
                return True
        else:
            from exception import RestRequestFailed

            raise RestRequestFailed(method, endpoint, response.status_code)

    def get_host(self):
        return self.host

