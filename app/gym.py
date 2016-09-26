import json
from calendar import timegm
from datetime import datetime

from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import request, current_app
from flask_restful import Resource, reqparse
from jose import jwt

from utils import non_empty_str
from authenticator import user_auth
from basic_response import InvalidResourceStructureError, InvalidResourceParameterError, \
    InvalidRequestError, DuplicateResourceCreationError, InvalidIdUpdateRequestError,  \
    AttemptedToAccessRestrictedResourceError, Response, NotSupportedOperationError
from database import gym_db as db, USER_LEVEL


def merchandise_price(price):
    if price is None or price == "":
        return {'amount': 0, 'currency': "CNY"}
    elif price.get('amount') is None or price.get('currency') is None:
        raise ValueError('Price is not well formatted')
    else:
        return price


def merchandise_expiry_info(expiry_info):
    if expiry_info is None or expiry_info == "":
        return {'startDate': "", 'expiryDate': ""}
    elif expiry_info.get('startDate') is None or expiry_info.get('expiryDate') is None:
        raise ValueError('ExpiryInfo is not well formatted')
    else:
        return expiry_info


def merchandise_schedule(schedule):
    if schedule is None or schedule == "":
        return {'start': "", 'end': ""}
    elif schedule.get('start') is None or schedule.get('end') is None:
        raise ValueError('Schedule is not well formatted')
    else:
        return schedule


class Merchandise(Resource):

    def get(self):
        def sanitize_merchandise_return_data(data=None):
            if data is not None:
                data.update({'_id': str(data.get("_id"))})
                if data.get('tag') is None:
                    data.update({'tag': ""})
                if data.get('detail') is None:
                    data.update({'detail': ""})
                if data.get('summary') is None:
                    data.update({'summary': ""})
                if data.get('schedule') is None:
                    data.update({'schedule': []})
                if data.get('imageURLs') is None:
                    data.update({'imageURLs': []})
                gym_id = data.get('owner')
                owner = db.gym.find_one({"_id": gym_id})
                owner.update({'_id': str(owner.get("_id"))})
                data.update({'owner': owner})
            return data

        parser = reqparse.RequestParser()
        parser.add_argument('id', location='args')
        parser.add_argument('keyword', location='args')
        parser.add_argument('owner', location='args')
        parser.add_argument('find', type=int, location='args')

        args = parser.parse_args()
        limit = args['find'] if args['find'] is not None else 0
        results = []
        query = None
        if args['id'] is not None:
            query = {"_id": ObjectId(args['id'])}
        if args['owner'] is not None:
            query = {"owner": ObjectId(args['owner'])}
        if args['keyword'] is not None:
            subquery = [{"name": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                        {"tag": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                        {"detail": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                        {"summary": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}}]
            query = {"$or": subquery}
        raw_results = db.merchandise.find(filter=query, limit=limit)
        for result in raw_results:
            results.append(sanitize_merchandise_return_data(result))
        current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
        if len(results) == 0:
            return json.loads(str(Response(success=False, data=results))), 404
        else:
            return json.loads(str(Response(success=True, data=results)))

    def put(self):

        def generate_update_merchandise_command():
            command = {}
            set_target = {}
            if args['type'] is not None:
                    set_target['type'] = args['type']
            if args['name'] is not None:
                    set_target['name'] = args['name']
            if args['detail'] is not None:
                    set_target['detail'] = args['detail']
            if args['owner'] is not None:
                gym_id = args['owner']
                try:
                    owner = db.gym.find_one({"_id": ObjectId(gym_id)})
                except TypeError:
                    raise InvalidResourceParameterError('owner', 'Merchandise')
                except InvalidId:
                    raise InvalidResourceParameterError('owner', 'Merchandise')
                if owner is None:
                    raise InvalidResourceParameterError('owner', 'Merchandise')
                else:
                    set_target['owner'] = owner.get("_id")
            if args['price'] is not None:
                set_target['price'] = args['price']
            if args['count'] is not None:
                set_target['count'] = args['count']
            if args['summary'] is not None:
                set_target['summary'] = args['summary']
            if args['tag'] is not None:
                set_target['tag'] = args['tag']
            if args['expiryInfo'] is not None:
                set_target['expiryInfo'] = args['expiryInfo']
            command['$set'] = set_target

            if args['schedule'] is not None:
                if len(args['schedule']) > 0:
                    if '$push' not in command:
                        command['$push'] = {}
                    command['$push']['schedule'] = {'$each': args['schedule']}

            if args['imageURLs'] is not None:
                if len(args['imageURLs']) > 0:
                    if '$push' not in command:
                        command['$push'] = {}
                    command['$push']['imageURLs'] = {'$each': args['imageURLs']}
            return command

        parser = reqparse.RequestParser()
        parser.add_argument('_id', required=True)
        parser.add_argument('type', type=int, choices=(1, 2), nullable=False)
        parser.add_argument('name', type=non_empty_str, nullable=False)
        parser.add_argument('detail', type=non_empty_str, nullable=False)
        parser.add_argument('owner', type=non_empty_str, nullable=False)
        parser.add_argument('tag', default="")
        parser.add_argument('count', type=int, default=-1, nullable=False)
        parser.add_argument('summary', default="")
        parser.add_argument('price', default={'amount': 0, 'currency': "CNY"}, type=merchandise_price)
        parser.add_argument('expiryInfo', default={'startDate': "", 'expiryDate': ""}, type=merchandise_expiry_info)
        parser.add_argument('schedule', type=merchandise_schedule, default=[], action='append')
        parser.add_argument('imageURLs', action='append', default=[])

        args = parser.parse_args()
        id_to_update = args['_id']
        self.validate_gym_privilege_for_merchandise(id_to_update)
        update_query = generate_update_merchandise_command()
        result = db.merchandise.update_one({"_id": ObjectId(id_to_update)}, update_query)
        if result.matched_count == 0:
            raise InvalidIdUpdateRequestError('Merchandise', args['_id'])
        return json.loads(str(Response(success=True, data=str(result.upserted_id))))

    # @user_auth.login_required
    def post(self):
        def validate_merchandise_entry_data_for_creation():
            parser.add_argument('type', type=int, required=True, choices=(1, 2), nullable=False)
            parser.add_argument('name', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('detail', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('owner', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('tag', default="")
            parser.add_argument('count', type=int, default=-1, nullable=False)
            parser.add_argument('summary', default="")
            parser.add_argument('price', default={'amount': 0, 'currency': "CNY"}, type=merchandise_price)
            parser.add_argument('expiryInfo', default={'startDate': "", 'expiryDate': ""}, type=merchandise_expiry_info)
            parser.add_argument('schedule', type=merchandise_schedule, default=[], action='append')
            parser.add_argument('imageURLs', action='append', default=[])

            args = parser.parse_args()
            gym_id = args['owner']
            owner = db.gym.find_one({"_id": ObjectId(gym_id)})
            if owner is None:
                raise InvalidResourceParameterError('owner', 'Merchandise')
            else:
                args.update({'owner': ObjectId(gym_id)})
            return args

        parser = reqparse.RequestParser()
        new_id = db.merchandise.insert_one(validate_merchandise_entry_data_for_creation()).inserted_id
        return json.loads(str(Response(success=True, data=str(new_id)))), 201

    @user_auth.login_required
    def delete(self, obj_id):
        self.validate_gym_privilege_for_merchandise(obj_id)
        result = db.merchandise.delete_one({"_id": ObjectId(obj_id)})
        if result.deleted_count < 1:
            return json.loads(str(Response(False, result.deleted_count))), 404
        return json.loads(str(Response(True, result.deleted_count)))

    @staticmethod
    def validate_gym_privilege_for_merchandise(id_to_validate):
        auth_type, token = request.headers['Authorization'].split(
            None, 1)
        claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256',
                           options={'verify_exp': False})
        gym_email = claim.get('user')
        gym = db.gym.find_one(filter={"email": gym_email})
        merchandise = db.merchandise.find_one(filter={"_id": ObjectId(id_to_validate)})
        if gym is None:
            raise AttemptedToAccessRestrictedResourceError("Merchandise")
        elif merchandise is not None and ObjectId(merchandise.get('owner')) != gym.get('_id'):
            raise AttemptedToAccessRestrictedResourceError("Merchandise")


class Gym(Resource):

    def get(self):
        def sanitize_gym_return_data(data=None):
            if data is not None:
                data.update({'_id': str(data.get("_id"))})
                if data.get('detail') is None:
                    data.update({'detail': ""})
                if data.get('smallLogo') is None:
                    data.update({'smallLogo': ""})
                if data.get('bigLogo') is None:
                    data.update({'bigLogo': ""})
                if data.get('services') is None:
                    data.update({'services': []})
                if data.get('announcements') is None:
                    data.update({'announcements': []})
                if data.get('equipments') is None:
                    data.update({'equipments': []})
                data.update({'geoLocation': data.get('geoLocation').get('coordinates')})
            return data

        parser = reqparse.RequestParser()
        parser.add_argument('id', help='id of gym', location='args')
        parser.add_argument('email', help='email of gym', location='args')
        parser.add_argument('address', help='address of gym', location='args')
        parser.add_argument('coordinates', help='coordinates of query center', location='args')
        parser.add_argument('max', type=float, help='max query distance in meter', location='args')
        parser.add_argument('min', type=float, help='min query distance in meter', location='args')
        parser.add_argument('keyword', help='query keyword for gym', location='args')
        parser.add_argument('find', type=int, help='number of desire response', location='args')
        args = parser.parse_args()
        limit = args['find'] if args['find'] is not None else 0
        results = []
        projection = {'password': 0}
        query = None
        if args['id'] is not None:
            query = {"_id": ObjectId(args['id'])}
            if request.headers['Authorization'] is not None:
                auth_type, token = request.headers['Authorization'].split(None, 1)
                claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256',
                                   options={'verify_exp': False})
                gym_email = claim.get('user')
                request_gym = db.gym.find_one(filter={"email": gym_email})
                if request_gym.get('_id') != ObjectId(args['id']):
                    projection['email'] = 0
            else:
                projection['email'] = 0
        elif args['email'] is not None:
            query = {'email': args['email']}
        elif args['address'] is not None:
            projection['email'] = 0
            query = {"address": {"$regex": ".*{}.*".format(args['address'].encode('utf-8'))}}
        elif args['coordinates'] is not None:
            projection['email'] = 0
            coordinates = [float(i) for i in args['coordinates'].split(',')]
            if len(coordinates) != 2:
                raise InvalidResourceStructureError('coordinates', 'gym query')
            near_target = {'$geometry': {'type': "Point", 'coordinates': coordinates}}
            if args['max'] is not None and args['max'] > 0:
                near_target['$maxDistance'] = args['max']
            if args['min'] is not None and args['min'] > 0:
                near_target['$minDistance'] = args['min']
            query = {'geoLocation': {'$near': near_target}}
        elif args['keyword'] is not None:
            projection['email'] = 0
            subquery = [{"name": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                        {"address": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                        {"detail": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}}]
            query = {"$or": subquery}

        raw_results = db.gym.find(filter=query, limit=limit, projection=projection)
        for result in raw_results:
            results.append(sanitize_gym_return_data(result))
        current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
        if len(results) == 0:
            return json.loads(str(Response(success=False, data=results))), 404
        else:
            return json.loads(str(Response(success=True, data=results)))

    def put(self):
        def validate_announcement_entry_data(data=None):
            if data is None:
                raise InvalidRequestError('announcement')
            if (data.get('content') is None or data.get('content') == "") and (
                    data.get('imageURLs') is None or data.get('imageURLs').__len__() == 0):
                raise InvalidResourceStructureError('content', 'announcement')
            if data.get('scope') is None or data.get('scope') > 2 or data.get('scope') < 1:
                raise InvalidResourceStructureError('scope', 'announcement')
            if data.get('actionType') is not None and data.get('actionType') != "":
                if data.get('actionType').get('type') is None or data.get('actionType').get('type') == "":
                    raise InvalidResourceStructureError('actionType', 'announcement')
                if data.get('actionType').get('content') is None or data.get('actionType').get('type') == "":
                    raise InvalidResourceStructureError('actionType', 'announcement')
            return data

        def generate_update_gym_command():
            command = {}
            set_target = {}
            if args['email'] is not None:
                set_target['email'] = args['email']
            if args['password'] is not None:
                raise NotSupportedOperationError('update password', 'Gym')
            if args['name'] is not None:
                set_target['name'] = args['name']
            if args['address'] is not None:
                set_target['address'] = args['address']
            if args['geoLocation'] is not None:
                if len(args['geoLocation']) != 2:
                    raise InvalidResourceStructureError('geoLocation', 'Gym update')
                else:
                    set_target['geoLocation'] = args['geoLocation']
            if args['smallLogo'] is not None:
                set_target['smallLogo'] = args['smallLogo']
            if args['bigLogo'] is not None:
                set_target['bigLogo'] = args['bigLogo']
            if args['detail'] is not None:
                set_target['detail'] = args['detail']
            command['$set'] = set_target

            if args['service'] is not None:
                if not isinstance(args['service'], list):
                    raise InvalidResourceParameterError('service', 'Gym')
                elif len(args['service']) > 0:
                    if '$push' not in command:
                        command['$push'] = {}
                    command['$push']['service'] = {'$each': args['service']}

            if args['announcements'] is not None:
                announcements = [validate_announcement_entry_data(announcement) for announcement in args['announcements']]
                if '$push' not in command:
                    command['$push'] = {}
                command['$push']['announcements'] = {'$each': announcements}

            return command

        def validate_privilege_for_gym():
            auth_type, token = request.headers['Authorization'].split(None, 1)
            claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256',
                               options={'verify_exp': False})
            gym_email = claim.get('user')
            request_gym = db.gym.find_one(filter={"email": gym_email})

            if request_gym is None:
                raise AttemptedToAccessRestrictedResourceError("Gym")
            elif request_gym.get('_id') != ObjectId(id_to_update):
                raise AttemptedToAccessRestrictedResourceError("Gym")

        parser = reqparse.RequestParser()
        parser.add_argument('_id', required=True)
        parser.add_argument('email', trim=True, type=non_empty_str, nullable=False)
        parser.add_argument('password', trim=True, type=non_empty_str, nullable=False)
        parser.add_argument('name', trim=True, type=non_empty_str, nullable=False)
        parser.add_argument('address', trim=True, type=non_empty_str, nullable=False)
        parser.add_argument('geoLocation', type=float, action='append', nullable=False)
        parser.add_argument('smallLogo')
        parser.add_argument('bigLogo')
        parser.add_argument('detail')
        parser.add_argument('service', type=dict, action='append')
        parser.add_argument('announcements', type=dict, action='append')

        args = parser.parse_args()
        id_to_update = args['_id']
        validate_privilege_for_gym()
        update_query = generate_update_gym_command()
        result = db.gym.update_one({"_id": ObjectId(id_to_update)}, update_query)
        if result.matched_count == 0:
            raise InvalidIdUpdateRequestError('Gym', id_to_update)
        return json.loads(str(Response(success=True, data=str(result.upserted_id))))

    def post(self):
        def validate_gym_entry_data_for_creation():
            parser.add_argument('email', required=True, trim=True, type=non_empty_str, nullable=False)
            parser.add_argument('password', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('name', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('address', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('geoLocation', type=float, required=True, action='append', nullable=False)
            parser.add_argument('smallLogo', help='smallLogo of gym')
            parser.add_argument('bigLogo', help='bigLogo of gym')
            parser.add_argument('detail', help='detail description of gym')
            args = parser.parse_args()
            coordinates = args['geoLocation']
            if len(coordinates) != 2:
                raise InvalidResourceStructureError('geoLocation', 'gym creation')
            args.update({'geoLocation': {'type': "Point", 'coordinates': coordinates}})
            duplicate = db.gym.find_one({"email": args['email']})
            if duplicate is not None:
                raise DuplicateResourceCreationError(args['email'], 'Gym')
            return args

        parser = reqparse.RequestParser()
        new_id = db.gym.insert_one(validate_gym_entry_data_for_creation()).inserted_id
        new_gym = db.gym.find_one({'_id': ObjectId(new_id)})

        issued_time = timegm(datetime.utcnow().utctimetuple())
        claims = {'iat': issued_time, 'user': new_gym['email'],
                  'level': USER_LEVEL['User']}
        jwt_token = str(jwt.encode(claims=claims, key=current_app.secret_key, algorithm='HS256'))
        return json.loads(str(Response(success=True, data={'jwt': jwt_token, 'id': str(new_id)}))), 201

