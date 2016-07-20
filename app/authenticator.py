from flask_restful import Resource
from flask_httpauth import HTTPTokenAuth
from passlib.hash import sha256_crypt
from database import admin as db
import base64
from jose import jwt, JWTError
import logging
from core import app
from calendar import timegm
from datetime import datetime


LOGGER = logging.getLogger()

admin_auth = HTTPTokenAuth(scheme='tnt-admin-auth-scheme', realm='admin')
resource_auth = HTTPTokenAuth(scheme='Bearer', realm='resource')
SESSION_TIMEOUT = 2628000


@admin_auth.verify_token
def verify_token(token):
    credentials = base64.decodestring(token).split(':')
    user = db.user.find_one(filter={"username": credentials[0]})
    if user is None:
        LOGGER.debug("user not found")
        return False
    return sha256_crypt.verify(credentials[1], user['hashed_password'])


@resource_auth.verify_token
def verify_token(token):
    try:
        jwt.decode(token=token, key=app.secret_key, algorithms='HS256')
    except JWTError as e:
        LOGGER.debug("%s, jwt not verified", str(e))
        return False
    return True


class AuthToken(Resource):
    @admin_auth.login_required
    def get(self):
        issued_time = timegm(datetime.utcnow().utctimetuple())
        return jwt.encode(claims={'exp': issued_time + SESSION_TIMEOUT, 'iat': issued_time}, key=app.secret_key, algorithm='HS256')
