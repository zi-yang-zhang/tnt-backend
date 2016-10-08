from calendar import timegm
from datetime import datetime

from flask import json
from jose import jwt

from authenticator import user_auth
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import request, current_app
from flask_restful import Resource, reqparse
from utils import non_empty_str
from database import user_db as db, USER_LEVEL

from basic_response import InvalidResourceStructureError, InvalidResourceParameterError, InvalidOperationError, \
    InvalidRequestError, DuplicateResourceCreationError, InvalidIdUpdateRequestError, AttemptedToDeleteInUsedResource, \
    AttemptedToAccessRestrictedResourceError, Response, ErrorResponse

GENDER = {1: 'male', 2: 'female', 3: 'unknown'}


class DuplicatedUsername(Exception):
    def __init__(self, username):
        self.code = "U1000"
        self.message = username + " already exists"


class DuplicatedUserEmail(Exception):
    def __init__(self, email):
        self.code = "U1001"
        self.message = email + " already exists"


class User(Resource):

    # @user_auth.login_required
    def get(self):
        def sanitize_user_return_data(data=None):
            if data is not None:
                data.update({'_id': str(data.get("_id"))})
                if data.get('firstName') is None:
                    data.update({'firstName': ""})
                if data.get('lastName') is None:
                    data.update({'lastName': ""})
                if data.get('gender') is None:
                    data.update({'gender': 3})
            return data

        parser = reqparse.RequestParser()
        parser.add_argument('id', location='args')
        parser.add_argument('email', location='args')
        parser.add_argument('keyword', location='args')
        parser.add_argument('find', type=int, help='number of desire response', location='args')
        args = parser.parse_args()
        limit = args['find'] if args['find'] is not None else 0
        results = []
        projection = {'authMethod': 0}
        query = None
        if args['id'] is not None:
            query = {"_id": ObjectId(args['id'])}
            if request.headers.get('Authorization') is not None:
                auth_type, token = request.headers['Authorization'].split(None, 1)
                claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256',
                                   options={'verify_exp': False})
                user_email = claim.get('user')
                request_user = db.user.find_one(filter={"email": user_email})
                if request_user is not None and request_user.get('_id') != ObjectId(args['id']):
                    projection['email'] = 0
            else:
                projection['email'] = 0
        elif args['email'] is not None:
            query = {'email': args['email']}
        elif args['keyword'] is not None:
            projection['email'] = 0
            subquery = [{"username": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}}]
            query = {"$or": subquery}

        raw_results = db.user.find(filter=query, limit=limit, projection=projection)
        for result in raw_results:
            results.append(sanitize_user_return_data(result))
        current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
        if len(results) == 0:
            return json.loads(str(Response(success=False, data=results))), 404
        else:
            return json.loads(str(Response(success=True, data=results)))


    def put(self):
        # def validate_announcement_entry_data(data=None):
        #     if data is None:
        #         raise InvalidRequestError('announcement')
        #     if (data.get('content') is None or data.get('content') == "") and (
        #             data.get('imageURLs') is None or data.get('imageURLs').__len__() == 0):
        #         raise InvalidResourceStructureError('content', 'announcement')
        #     if data.get('scope') is None or data.get('scope') > 2 or data.get('scope') < 1:
        #         raise InvalidResourceStructureError('scope', 'announcement')
        #     if data.get('actionType') is not None and data.get('actionType') != "":
        #         if data.get('actionType').get('type') is None or data.get('actionType').get('type') == "":
        #             raise InvalidResourceStructureError('actionType', 'announcement')
        #         if data.get('actionType').get('content') is None or data.get('actionType').get('type') == "":
        #             raise InvalidResourceStructureError('actionType', 'announcement')
        #     return data
        #
        # def generate_update_gym_command():
        #     command = {}
        #     set_target = {}
        #     if args['email'] is not None:
        #         set_target['email'] = args['email']
        #     if args['password'] is not None:
        #         raise NotSupportedOperationError('update password', 'Gym')
        #     if args['name'] is not None:
        #         set_target['name'] = args['name']
        #     if args['address'] is not None:
        #         set_target['address'] = args['address']
        #     if args['geoLocation'] is not None:
        #         if len(args['geoLocation']) != 2:
        #             raise InvalidResourceStructureError('geoLocation', 'Gym update')
        #         else:
        #             set_target['geoLocation'] = args['geoLocation']
        #     if args['smallLogo'] is not None:
        #         set_target['smallLogo'] = args['smallLogo']
        #     if args['bigLogo'] is not None:
        #         set_target['bigLogo'] = args['bigLogo']
        #     if args['detail'] is not None:
        #         set_target['detail'] = args['detail']
        #     command['$set'] = set_target
        #
        #     if args['service'] is not None:
        #         if not isinstance(args['service'], list):
        #             raise InvalidResourceParameterError('service', 'Gym')
        #         elif len(args['service']) > 0:
        #             if '$push' not in command:
        #                 command['$push'] = {}
        #             command['$push']['service'] = {'$each': args['service']}
        #
        #     if args['announcements'] is not None:
        #         announcements = [validate_announcement_entry_data(announcement) for announcement in args['announcements']]
        #         if '$push' not in command:
        #             command['$push'] = {}
        #         command['$push']['announcements'] = {'$each': announcements}
        #
        #     return command
        #
        # def validate_privilege_for_gym():
        #     auth_type, token = request.headers['Authorization'].split(None, 1)
        #     claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256',
        #                        options={'verify_exp': False})
        #     gym_email = claim.get('user')
        #     request_gym = db.gym.find_one(filter={"email": gym_email})
        #
        #     if request_gym is None:
        #         raise AttemptedToAccessRestrictedResourceError("Gym")
        #     elif request_gym.get('_id') != ObjectId(id_to_update):
        #         raise AttemptedToAccessRestrictedResourceError("Gym")
        #
        # parser = reqparse.RequestParser()
        # parser.add_argument('_id', required=True)
        # parser.add_argument('email', trim=True, type=non_empty_str, nullable=False)
        # parser.add_argument('password', trim=True, type=non_empty_str, nullable=False)
        # parser.add_argument('name', trim=True, type=non_empty_str, nullable=False)
        # parser.add_argument('address', trim=True, type=non_empty_str, nullable=False)
        # parser.add_argument('geoLocation', type=float, action='append', nullable=False)
        # parser.add_argument('smallLogo')
        # parser.add_argument('bigLogo')
        # parser.add_argument('detail')
        # parser.add_argument('service', type=dict, action='append')
        # parser.add_argument('announcements', type=dict, action='append')
        #
        # args = parser.parse_args()
        # id_to_update = args['_id']
        # validate_privilege_for_gym()
        # update_query = generate_update_gym_command()
        # result = db.gym.update_one({"_id": ObjectId(id_to_update)}, update_query)
        # if result.matched_count == 0:
        #     raise InvalidIdUpdateRequestError('Gym', id_to_update)
        # return json.loads(str(Response(success=True, data=str(result.upserted_id))))
        pass

    def post(self):
        def validate_user_entry_data_for_creation():
            parser.add_argument('username', required=True, trim=True, type=non_empty_str, nullable=False)
            parser.add_argument('email', required=True, trim=True, type=non_empty_str, nullable=False)
            parser.add_argument('password', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('firstName', type=non_empty_str, nullable=False, default="")
            parser.add_argument('lastName', type=non_empty_str, nullable=False, default="")
            parser.add_argument('age', type=int, nullable=False, default=-1)
            parser.add_argument('gender', type=int, choices=(1, 2, 3), nullable=False, default=3)
            args = parser.parse_args()
            duplicate_email = db.user.find_one({"email": args['email']})
            duplicate_username = db.user.find_one({"username": args['username']})
            if duplicate_email is not None:
                raise DuplicatedUserEmail(args['email'])
            if duplicate_username is not None:
                raise DuplicatedUsername(args['username'])
            args['authMethod'] = {'type': "password", 'method': args['password']}
            del args['password']
            return args

        parser = reqparse.RequestParser()
        new_id = db.user.insert_one(validate_user_entry_data_for_creation()).inserted_id
        new_user = db.user.find_one({'_id': ObjectId(new_id)})
        issued_time = timegm(datetime.utcnow().utctimetuple())
        claims = {'iat': issued_time, 'user': new_user['email'],
                  'level': USER_LEVEL['User']}
        jwt_token = str(jwt.encode(claims=claims, key=current_app.secret_key, algorithm='HS256'))
        return json.loads(str(Response(success=True, data={'jwt': jwt_token}))), 201
