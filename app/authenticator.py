import base64
from calendar import timegm
from datetime import datetime

from flask import request, make_response, current_app as app
from flask_httpauth import HTTPTokenAuth, HTTPDigestAuth, MultiAuth
from flask_restful import Resource
from jose import jwt, JWTError
from passlib.hash import sha256_crypt

from database import USER_LEVEL
from database import admin_db as db

from flask import Blueprint
from flask_restful import Api

auth_api = Blueprint('auth_api', __name__)
auth_api_router = Api(auth_api)

TNT_USER_AUTH_SCHEME = 'TNT-User-Auth'
WECHAT_USER_AUTH_SCHEME = 'Wechat-User-Auth'

TNT_GYM_AUTH_SCHEME = 'TNT-Gym-Auth'
WECHAT_Gym_AUTH_SCHEME = 'Wechat-Gym-Auth'

admin_token_auth = HTTPTokenAuth(scheme='tnt-admin-auth-scheme', realm='admin')
resource_access_auth = HTTPTokenAuth(scheme='Bearer', realm='resource')
user_auth = HTTPTokenAuth(scheme='Bearer', realm='user')
user_login_pw_authenticator = HTTPDigestAuth(scheme=TNT_USER_AUTH_SCHEME, realm='user', use_ha1_pw=True)
user_login_authenticator = MultiAuth(main_auth=user_login_pw_authenticator)

gym_login_pw_authenticator = HTTPDigestAuth(scheme=TNT_GYM_AUTH_SCHEME, realm='gym', use_ha1_pw=True)
gym_login_authenticator = MultiAuth(main_auth=gym_login_pw_authenticator)

SESSION_TIMEOUT = 2628000

AUTHENTICATION_TYPE = ["password", "wechat"]


def authentication_method(auth_method):
    if auth_method is None or auth_method == "" or auth_method.get('type') is None or auth_method.get(
            'type') not in AUTHENTICATION_TYPE or auth_method.get('method') is None or auth_method.get('method') == "":
        raise ValueError('Authentication mal-formatted')
    else:
        return auth_method


@admin_token_auth.verify_token
def verify_token(token):
    username, password = base64.decodestring(token).split(':')
    user = db.user.find_one(filter={"username": username})
    if user is None:
        app.logger.error("user %s not found", username)
        return False
    return sha256_crypt.verify(password, user['hashed_password'])


@resource_access_auth.verify_token
def verify_token(token):
    try:
        claim = jwt.decode(token=token, key=app.secret_key, algorithms='HS256', options={'verify_exp': False})
        app.logger.info('Request received from %s, level %s', claim.get('user'), claim.get('level'))
    except JWTError as e:
        app.logger.error("jwt not verified: %s", type(e).__name__)
        return False
    return True


class UserAuthToken(Resource):
    @user_login_authenticator.login_required
    def get(self):
        issued_time = timegm(datetime.utcnow().utctimetuple())
        claims = {'iat': issued_time, 'email': user_login_pw_authenticator.username(), 'level': USER_LEVEL['User']}
        return jwt.encode(claims=claims, key=app.secret_key, algorithm='HS512')


class GymAuthToken(Resource):
    @gym_login_authenticator.login_required
    def get(self):
        issued_time = timegm(datetime.utcnow().utctimetuple())
        claims = {'iat': issued_time, 'email': gym_login_pw_authenticator.username(), 'level': USER_LEVEL['User']}
        return jwt.encode(claims=claims, key=app.secret_key, algorithm='HS512')


# class AdminAuthToken(Resource):
#     @admin_token_auth.login_required
#     def post(self):
#         args = request.get_json()
#         auth_type, token = request.headers['Authorization'].split(
#             None, 1)
#         username, password = base64.decodestring(token).split(':')
#         if args.get('username') is None:
#             return make_response('username missing in payload', 400)
#         issued_time = timegm(datetime.utcnow().utctimetuple())
#         claims = {'exp': issued_time + SESSION_TIMEOUT, 'iat': issued_time, 'user': username, 'level': USER_LEVEL['Admin']}
#         return jwt.encode(claims=claims, key=app.secret_key, algorithm='HS256')


class WechatAuthToken(Resource):
    def post(self):
        pass


auth_api_router.add_resource(UserAuthToken, '/api/login/user')
auth_api_router.add_resource(GymAuthToken, '/api/login/gym')
