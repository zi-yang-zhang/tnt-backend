import base64
from calendar import timegm
from datetime import datetime

from flask import request, make_response, current_app as app
from flask_httpauth import HTTPTokenAuth
from flask_restful import Resource
from jose import jwt, JWTError
from passlib.hash import sha256_crypt
import requests

from database import admin as db

admin_token_auth = HTTPTokenAuth(scheme='tnt-admin-auth-scheme', realm='admin')
resource_access_auth = HTTPTokenAuth(scheme='Bearer', realm='resource')
user_auth = HTTPTokenAuth(scheme='Bearer', realm='user')

SESSION_TIMEOUT = 2628000

USER_LEVEL = {'DBA': 0, 'SystemAdmin': 1, 'Admin': 2, 'PowerUser': 3, 'User': 4, 'Guest': 5}


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
        app.logger.error("jwt not verified: %s",  type(e).__name__)
        return False
    return True


class AdminAuthToken(Resource):
    @admin_token_auth.login_required
    def post(self):
        args = request.get_json()
        auth_type, token = request.headers['Authorization'].split(
            None, 1)
        username, password = base64.decodestring(token).split(':')
        if args.get('username') is None:
            return make_response('username missing in payload', 400)
        issued_time = timegm(datetime.utcnow().utctimetuple())
        claims = {'exp': issued_time + SESSION_TIMEOUT, 'iat': issued_time, 'user': username, 'level': USER_LEVEL['Admin']}
        return jwt.encode(claims=claims, key=app.secret_key, algorithm='HS256')


class WechatAuthToken(Resource):
    def post(self):
        pass