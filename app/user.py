from calendar import timegm
from datetime import datetime

from bson.objectid import ObjectId
from flask import json
from flask import make_response
from flask import request, current_app, jsonify
from flask_restful import Resource, reqparse
from jose import jwt

from exception import InvalidResourceStructureError, InvalidResourceParameterError, InvalidIdUpdateRequestError, \
    AuthenticationUserNotFound, AuthenticationUserAuthTypeError
from authenticator import user_login_pw_authenticator, AUTHENTICATION_TYPE, authentication_method
from basic_response import Response
from database import user_db as db, USER_LEVEL
from utils import non_empty_str, non_empty_and_no_space_str
from im_engine import create_im_user

GENDER = {1: 'male', 2: 'female', 3: 'unknown'}


class DuplicatedUsername(Exception):
    def __init__(self, username):
        self.code = "U1000"
        self.message = username + " already exists"


class DuplicatedUserEmail(Exception):
    def __init__(self, email):
        self.code = "U1001"
        self.message = email + " already exists"


@user_login_pw_authenticator.get_password
def get_pw(username):
    user = db.user.find_one({"username": username})
    if not user:
        raise AuthenticationUserNotFound
    elif user['authMethod']['type'] != AUTHENTICATION_TYPE[0]:
        raise AuthenticationUserAuthTypeError(AUTHENTICATION_TYPE[0], user['authMethod']['type'])
    else:
        return user['authMethod']['method']


class User(Resource):
    # @user_auth.login_required
    def get(self):
        def sanitize_user_return_data(data=None):
            if data is not None:
                data.update({'_id': str(data.get("_id"))})
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
        def generate_update_user_query():
            command = {}
            set_target = {}
            if args['nickname'] is not None:
                set_target['nickname'] = args['nickname']
            if args['firstName'] is not None:
                set_target['firstName'] = args['firstName']
            if args['lastName'] is not None:
                set_target['lastName'] = args['lastName']
            if args['age'] is not None:
                set_target['age'] = args['age']
            if args['gender'] is not None:
                set_target['gender'] = args['gender']
            if args['height'] is not None:
                set_target['height'] = args['height']
            if args['tel'] is not None:
                set_target['tel'] = args['tel']
            if args['currentLocation'] is not None:
                if len(args['currentLocation']) != 2:
                    raise InvalidResourceStructureError('currentLocation', 'Gym update')
                else:
                    set_target['geoLocation.coordinates'] = args['currentLocation']

            command['$set'] = set_target
            if args['favoriteGym'] is not None:
                if not isinstance(args['favoriteGym'], list):
                    raise InvalidResourceParameterError('favoriteGym', 'User')
                elif len(args['favoriteGym']) > 0:
                    if '$push' not in command:
                        command['$push'] = {}
                    command['$push']['favoriteGym'] = {'$each': args['favoriteGym']}
            return command

        parser = reqparse.RequestParser()
        parser.add_argument('nickname', trim=True, type=non_empty_and_no_space_str, nullable=False)
        parser.add_argument('firstName', type=non_empty_str, nullable=False, default="")
        parser.add_argument('lastName', type=non_empty_str, nullable=False, default="")
        parser.add_argument('age', type=int, nullable=False, default=-1)
        parser.add_argument('gender', type=int, choices=(1, 2, 3), nullable=False, default=3)
        parser.add_argument('height', type=float, nullable=False, default=-1)
        parser.add_argument('tel', type=str, nullable=False)
        parser.add_argument('currentLocation', type=float, action='append', nullable=False)
        parser.add_argument('favoriteGym', type=str, nullable=False)

        args = parser.parse_args()
        id_to_update = args['_id']
        update_query = generate_update_user_query()
        result = db.user.update_one({"_id": ObjectId(id_to_update)}, update_query)
        if result.matched_count == 0:
            raise InvalidIdUpdateRequestError('User', id_to_update)
        return json.loads(str(Response(success=True, data=str(result.upserted_id))))

    def post(self):
        def validate_user_entry_data_for_creation():
            duplicate_email = db.user.find_one({"email": args['email']})
            duplicate_username = db.user.find_one({"username": args['username']})
            if duplicate_email is not None:
                raise DuplicatedUserEmail(args['email'])
            if duplicate_username is not None:
                raise DuplicatedUsername(args['username'])
            if args['authMethod']['type'] == AUTHENTICATION_TYPE[0]:
                args['authMethod']['method'] = user_login_pw_authenticator.generate_ha1(args['username'],
                                                                                        args['authMethod']['method'])
        parser = reqparse.RequestParser()
        parser.add_argument('username', required=True, trim=True, type=non_empty_and_no_space_str, nullable=False)
        parser.add_argument('email', required=True, trim=True, type=non_empty_and_no_space_str, nullable=False)
        parser.add_argument('authMethod', required=True, type=authentication_method, nullable=False)
        parser.add_argument('nickname', trim=True, type=non_empty_and_no_space_str, nullable=False)
        parser.add_argument('firstName', type=non_empty_str, nullable=False, default="")
        parser.add_argument('lastName', type=non_empty_str, nullable=False, default="")
        parser.add_argument('age', type=int, nullable=False, default=-1)
        parser.add_argument('gender', type=int, choices=(1, 2, 3), nullable=False, default=3)
        args = parser.parse_args(strict=True)
        validate_user_entry_data_for_creation()
        db.user.insert_one(args)
        issued_time = timegm(datetime.utcnow().utctimetuple())
        claims = {'iat': issued_time, 'username': args['username'], 'level': USER_LEVEL['User']}
        # create_im_user(user_id=new_id, username=args['username'], email=args['email'], nickname=args['nickname'])
        return make_response(Response(success=True, data={'jwt': jwt.encode(claims=claims, key=current_app.secret_key, algorithm='HS512')}).get_resp(), 201)
