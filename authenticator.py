from flask_restful import Resource
from flask_httpauth import HTTPTokenAuth
import passlib
from database import admin as db
import bson.json_util
import base64
from jose import jwt, JWTError
import logging
from core import app
from calendar import timegm
from datetime import datetime
from flask import send_from_directory


LOGGER = logging.getLogger()

admin_auth = HTTPTokenAuth(scheme='tnt-admin-auth-scheme', realm='admin')
resource_auth = HTTPTokenAuth(scheme='Bearer', realm='resource')
SESSION_TIMEOUT = 10000000


@admin_auth.verify_token
def verify_token(token):
    LOGGER.debug('token :' + token)
    credentials = base64.decodestring(token).split(':')
    LOGGER.debug('credentials :' + str(credentials))
    user = db.user.find_one(filter={"username": credentials[0]})
    LOGGER.debug(user)
    if user is None:
        LOGGER.debug("user not found")
        return False
    return credentials[1] == user['hashed_password']


@resource_auth.verify_token
def verify_token(token):
    try:
        claim = jwt.decode(token=token, key=app.secret_key, algorithms='HS256')
        LOGGER.debug("claim extracted: %s", claim)
    except JWTError as e:
        LOGGER.debug("%s, jwt not verified", str(e))
        return False
    return True


@app.route('/dashboard')
@resource_auth.login_required
def dashboard():
    return send_from_directory('template', 'app.html')


class TestResource(Resource):
    @resource_auth.login_required
    def get(self):
        return 'protected resource'


class AuthToken(Resource):

    @admin_auth.login_required
    def get(self):
        issued_time = timegm(datetime.utcnow().utctimetuple())
        return jwt.encode(claims={'exp': issued_time + SESSION_TIMEOUT, 'iat': issued_time}, key=app.secret_key, algorithm='HS256')
