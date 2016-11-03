import base64
import os
import random
import string

from bson import ObjectId
from flask_restful import Resource

from database import user_db
from openfire_rest_api import ApiFactory, Api
from flask import current_app


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def create_im_user(user_id, email, username, nickname):
    current_app.logger.info('Creating im user for {}'.format(email))
    generated_chat_password = id_generator(size=32)
    current_app.logger.debug('Generated im user credentials: {}, {}'.format(username, generated_chat_password))
    new_chat_user = {'username': username, 'password': generated_chat_password, 'name': nickname,
                     'email': email}
    auth = 'Basic ' + base64.b64encode(os.environ['CHAT_SERVER_ADMIN'] + ':' + os.environ['CHAT_SERVER_ADMIN_PW'])
    api = ApiFactory(api=Api.User, host=os.environ['CHAT_SERVER'], auth=auth).get_api()
    success = api.create_user(new_chat_user)
    if success:
        update_command = {'$set': {'chatServerPassword': generated_chat_password}}
        user_db.user.update({"_id": ObjectId(user_id)}, update_command)


class IMServerUser(Resource):
    pass
