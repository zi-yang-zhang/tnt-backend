import json

from bson.objectid import ObjectId
from flask import Blueprint, request, current_app
from flask_restful import Resource, reqparse, Api
from jose import jwt
from pymongo import ASCENDING, DESCENDING

import exception
import time_tools
from authenticator import gym_auth, gym_login_pw_authenticator, AUTHENTICATION_TYPE, authentication_method, CLIENT_TYPE
from basic_response import Response
from database import gym_db as db
from utils import non_empty_str, bearer_header_str

EXPIRY_INFO_TYPE = {"by_count": 1, "by_duration": 2}


@gym_login_pw_authenticator.get_password
def verify_pw(email):
    gym = db.gym.find_one({"email": email})
    if not gym:
        raise exception.AuthenticationUserNotFound
    elif gym['authMethod']['type'] != AUTHENTICATION_TYPE[0]:
        raise exception.AuthenticationUserAuthTypeError(AUTHENTICATION_TYPE[0], gym['authMethod']['type'])
    else:
        return gym['authMethod']['method']


def merchandise_price(price):
    if price is None or price == "":
        return {'amount': 0, 'currency': "CNY"}
    elif price.get('amount') is None or price.get('currency') is None:
        raise ValueError('Price is not well formatted')
    else:
        return price


def merchandise_expiry_info(expiry_info):
    if expiry_info.get('type') is None or not isinstance(expiry_info.get('type'), int) or expiry_info.get(
            'type') < 0 or expiry_info.get('type') > 2:
        raise ValueError('ExpiryInfo is not well formatted')
    else:
        if expiry_info.get('type') == EXPIRY_INFO_TYPE["by_count"] and expiry_info.get(
                'startDate') is not None and expiry_info.get('expiryDate') is not None and expiry_info.get('count') is not None and isinstance(expiry_info.get('count'), int) and expiry_info.get('count') > 0:
            import dateutil.parser
            from dateutil.tz import tzutc
            if expiry_info.get('startDate') != "":
                start_date = dateutil.parser.parse(expiry_info.get('startDate'), tzinfos=tzutc)
                expiry_info.update({'startDate': start_date})
            if expiry_info.get('expiryDate') != "":
                exp_date = dateutil.parser.parse(expiry_info.get('expiryDate'), tzinfos=tzutc)
                expiry_info.update({'expiryDate': exp_date})
            return expiry_info
        elif expiry_info.get('type') == EXPIRY_INFO_TYPE["by_duration"] and expiry_info.get('duration') is not None and expiry_info.get('duration') > 0:
            return expiry_info
        else:
            raise ValueError('ExpiryInfo is not well formatted')


def merchandise_schedule(schedule):
    if schedule is None or schedule == "":
        return {'start': "", 'end': ""}
    elif schedule.get('start') is None or schedule.get('end') is None:
        raise ValueError('Schedule is not well formatted')
    else:
        return schedule


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
        created_date_iso = data.get('createdDate').isoformat()
        if data.get('duration') == -1:
            data.update({'exp_remain': -1})
        else:
            data.update({'exp_remain': time_tools.get_remaining_time_in_second(data.get('createdDate'), data.get('duration'))})
        data.update({'createdDate': created_date_iso})
        expiry_info = data.get('expiryInfo')
        if expiry_info.get('type') == EXPIRY_INFO_TYPE["by_count"]:
            if expiry_info.get('startDate') != "":
                start_date_iso = expiry_info.get('startDate').isoformat()
                expiry_info.update({'startDate': start_date_iso})
            if expiry_info.get('expiryDate') != "":
                exp_date_iso = expiry_info.get('expiryDate').isoformat()
                expiry_info.update({'expiryDate': exp_date_iso})
            data.update({'expiryInfo': expiry_info})
        data.update({'owner': str(gym_id)})
    return data


class Merchandise(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', location='args')
        parser.add_argument('keyword', location='args')
        parser.add_argument('owner', location='args')
        parser.add_argument('find', type=int, location='args')

        args = parser.parse_args()
        limit = args['find'] if args['find'] is not None else 0
        results = []
        query = None
        if request.headers.get('Authorization'):
            auth_type, token = request.headers['Authorization'].split(None, 1)
            claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS512',
                               options={'verify_exp': False})
            query = {"owner": ObjectId(claim.get('id'))}
        elif args['id'] is not None:
            query = {"_id": ObjectId(args['id'])}
        else:
            if args['owner'] is not None:
                query = {"owner": ObjectId(args['owner'])}
            if args['keyword'] is not None:
                query = {}
                subquery = [{"name": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                            {"tag": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                            {"detail": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                            {"summary": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}}]
                query["$or"] = subquery
        if query is None:
            return json.loads(str(Response(success=False, data=results))), 200
        raw_results = db.merchandise.find(filter=query, limit=limit)
        for result in raw_results:
            results.append(sanitize_merchandise_return_data(result))
        current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
        if len(results) == 0:
            return json.loads(str(Response(success=False, data=results))), 404
        else:
            return json.loads(str(Response(success=True, data=results)))

    @gym_auth.login_required
    def put(self):
        def generate_update_merchandise_command():
            command = {}
            set_target = {}
            if args['name'] is not None:
                set_target['name'] = args['name']
            if args['active'] is not None:
                set_target['active'] = args['active']
            if args['detail'] is not None:
                set_target['detail'] = args['detail']
            if args['price'] is not None:
                set_target['price'] = merchandise_price(args['price'])
            if args['summary'] is not None:
                set_target['summary'] = args['summary']
            if args['tag'] is not None:
                set_target['tag'] = args['tag']
            if args['expiryInfo'] is not None:
                set_target['expiryInfo'] = merchandise_expiry_info(args['expiryInfo'])
            command['$set'] = set_target

            if args['schedule'] is not None:
                if len(args['schedule']) > 0:
                    if '$push' not in command:
                        command['$push'] = {}
                    command['$push']['schedule'] = {'$each': merchandise_schedule(args['schedule'])}

            if args['imageURLs'] is not None:
                if len(args['imageURLs']) > 0:
                    if '$push' not in command:
                        command['$push'] = {}
                    command['$push']['imageURLs'] = {'$each': args['imageURLs']}
            return command

        parser = reqparse.RequestParser()
        parser.add_argument('_id', required=True)
        parser.add_argument('name', type=non_empty_str, nullable=False)
        parser.add_argument('detail', type=non_empty_str, nullable=False)
        parser.add_argument('expiryInfo', type=merchandise_expiry_info, nullable=False)
        parser.add_argument('sku', default="", type=str, nullable=False)
        parser.add_argument('tag', default="")
        parser.add_argument('summary', default="")
        parser.add_argument('price', default={'amount': 0, 'currency': "CNY"}, type=merchandise_price)
        parser.add_argument('schedule', type=merchandise_schedule, default=[], action='append')
        parser.add_argument('imageURLs', action='append', default=[])
        parser.add_argument('active', nullable=False, type=bool)

        args = parser.parse_args()
        id_to_update = args['_id']
        self.validate_gym_privilege_for_merchandise(id_to_update)
        update_query = generate_update_merchandise_command()
        result = db.merchandise.update_one({"_id": ObjectId(id_to_update)}, update_query)
        if result.matched_count == 0:
            raise exception.InvalidIdUpdateRequestError('Merchandise', args['_id'])
        return json.loads(str(Response(success=True, data=str(result.upserted_id))))

    @gym_auth.login_required
    def post(self):
        def validate_merchandise_entry_data_for_creation():
            parser.add_argument('name', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('detail', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('expiryInfo', required=True, type=merchandise_expiry_info, nullable=False)
            parser.add_argument('duration', required=True, type=long, nullable=False)
            parser.add_argument('sku', default="", type=str, nullable=False)
            parser.add_argument('tag', default="")
            parser.add_argument('summary', default="")
            parser.add_argument('price', default={'amount': 0, 'currency': "CNY"}, type=merchandise_price)
            parser.add_argument('schedule', type=merchandise_schedule, default=[], action='append')
            parser.add_argument('imageURLs', action='append', default=[])

            args = parser.parse_args()
            auth_type, token = request.headers['Authorization'].split(
                None, 1)
            claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS512',
                               options={'verify_exp': False})
            gym_id = claim.get('id')
            owner = db.gym.find_one({"_id": ObjectId(gym_id)})
            if owner is None:
                raise exception.InvalidResourceParameterError('owner', 'Merchandise')
            else:
                args.update({'owner': owner['_id']})
            return args
        parser = reqparse.RequestParser()
        merchandise = validate_merchandise_entry_data_for_creation()
        merchandise["createdDate"] = time_tools.get_current_time()
        merchandise["active"] = True
        new_id = db.merchandise.insert_one(merchandise).inserted_id
        new_merchandise = db.merchandise.find_one({"_id": new_id})

        return json.loads(str(Response(success=True, data=sanitize_merchandise_return_data(new_merchandise)))), 201

    @gym_auth.login_required
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
        claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS512',
                           options={'verify_exp': False})
        gym_id = claim.get('id')
        gym = db.gym.find_one(filter={"_id": ObjectId(gym_id)})
        merchandise = db.merchandise.find_one(filter={"_id": ObjectId(id_to_validate)})
        if gym is None:
            raise exception.AttemptedToAccessRestrictedResourceError("Merchandise")
        elif merchandise is not None and ObjectId(merchandise.get('owner')) != gym.get('_id'):
            raise exception.AttemptedToAccessRestrictedResourceError("Merchandise")


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
        else:
            for announcement in data.get('announcements'):
                announcement.update({'_id': str(announcement.get('_id'))})
                announcement.update({'createdDate': announcement.get('createdDate').isoformat()})
        if data.get('equipments') is None:
            data.update({'equipments': []})
        lng = data.get('geoLocation').get('coordinates')[0]
        lat = data.get('geoLocation').get('coordinates')[1]
        data.update({'geoLocation': {'lng': lng, 'lat': lat}})
    return data


class Gym(Resource):

    def get(self):
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
        projection = {'authMethod': 0}
        query = None
        if args['id'] is not None:
            query = {"_id": ObjectId(args['id'])}
            if request.headers.get('Authorization') is not None:
                auth_type, token = request.headers['Authorization'].split(None, 1)
                claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS512',
                                   options={'verify_exp': False})
                gym_id = claim.get('id')
                request_gym = db.gym.find_one(filter={"_id": ObjectId(gym_id)})
                if request_gym is not None and request_gym.get('_id') != ObjectId(args['id']):
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
                raise exception.InvalidResourceStructureError('coordinates', 'gym query')
            near_target = {'$geometry': {'type': "Point", 'coordinates': coordinates}}
            if args['max'] is not None and args['max'] > 0:
                near_target['$maxDistance'] = args['max']
            if args['min'] is not None and args['min'] > 0:
                near_target['$minDistance'] = args['min']
            query = {'geoLocation': {'$near': near_target}}
        if args['keyword'] is not None:
            if query is None:
                query = {}
            projection['email'] = 0
            subquery = [{"name": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                        {"address": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}},
                        {"detail": {"$regex": ".*{}.*".format(args['keyword'].encode('utf-8'))}}]
            query["$or"] = subquery
        if query is None:
            return json.loads(str(Response(success=False, data=results))), 404
        raw_results = db.gym.find(filter=query, limit=limit, projection=projection)
        for result in raw_results:
            results.append(sanitize_gym_return_data(result))
        current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
        if len(results) == 0:
            return json.loads(str(Response(success=False, data=results))), 404
        else:
            return json.loads(str(Response(success=True, data=results)))

    @gym_auth.login_required
    def post(self):
        def generate_update_gym_command():
            command = {}
            set_target = {}
            if args['email'] is not None:
                set_target['email'] = args['email']
            if args['name'] is not None:
                set_target['name'] = args['name']
            if args['address'] is not None:
                set_target['address'] = args['address']
            if args['geoLocation'] is not None:
                if len(args['geoLocation']) != 2:
                    raise exception.InvalidResourceStructureError('geoLocation', 'Gym update')
                else:
                    set_target['geoLocation.coordinates'] = args['geoLocation']
            if args['smallLogo'] is not None:
                set_target['smallLogo'] = args['smallLogo']
            if args['bigLogo'] is not None:
                set_target['bigLogo'] = args['bigLogo']
            if args['detail'] is not None:
                set_target['detail'] = args['detail']
            if set_target != {}:
                command['$set'] = set_target

            if args['service'] is not None:
                if not isinstance(args['service'], list):
                    raise exception.InvalidResourceParameterError('service', 'Gym')
                elif len(args['service']) > 0:
                    if '$push' not in command:
                        command['$push'] = {}
                    command['$push']['service'] = {'$each': args['service']}

            if args['announcements'] is not None:
                announcements = [validate_announcement_entry_data(announcement) for announcement in
                                 args['announcements']]
                if '$push' not in command:
                    command['$push'] = {}
                command['$push']['announcements'] = {'$each': announcements}
            return command

        parser = reqparse.RequestParser()
        parser.add_argument('email', trim=True, type=non_empty_str, nullable=False)
        parser.add_argument('name', trim=True, type=non_empty_str, nullable=False)
        parser.add_argument('address', trim=True, type=non_empty_str, nullable=False)
        parser.add_argument('geoLocation', type=float, action='append', nullable=False)
        parser.add_argument('smallLogo')
        parser.add_argument('bigLogo')
        parser.add_argument('detail', type=str, nullable=False)
        parser.add_argument('service', type=dict, action='append')
        parser.add_argument('announcements', type=dict, action='append')
        parser.add_argument('Authorization', trim=True, type=bearer_header_str, nullable=False, location='headers', required=True, help='Needs to be logged in to delete')

        args = parser.parse_args()
        token = args['Authorization']
        claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS512',
                           options={'verify_exp': False})
        id_to_update = claim.get('id')
        update_query = generate_update_gym_command()
        result = db.gym.update_one({"_id": ObjectId(id_to_update)}, update_query)
        if result.modified_count > 0:
            result = db.gym.find_one({"_id": ObjectId(id_to_update)})
            return json.loads(str(Response(success=True, data=sanitize_gym_return_data(result)))), 200
        else:
            return json.loads(str(Response(success=True))), 304

    def put(self):
        def validate_gym_entry_data_for_creation():
            parser.add_argument('email', required=True, trim=True, type=non_empty_str, nullable=False)
            parser.add_argument('authMethod', required=True, type=authentication_method, nullable=False)
            parser.add_argument('name', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('address', required=True, type=non_empty_str, nullable=False)
            parser.add_argument('geoLocation', type=float, required=True, action='append', nullable=False)
            parser.add_argument('smallLogo', help='smallLogo of gym')
            parser.add_argument('bigLogo', help='bigLogo of gym')
            parser.add_argument('detail', help='detail description of gym')
            args = parser.parse_args()
            coordinates = args['geoLocation']
            if len(coordinates) != 2:
                raise exception.InvalidResourceStructureError('geoLocation', 'gym creation')
            args.update({'geoLocation': {'type': "Point", 'coordinates': coordinates}})
            duplicate = db.gym.find_one({"email": args['email']})
            if duplicate is not None:
                raise exception.DuplicateResourceCreationError(args['email'], 'Gym')
            if args['authMethod']['type'] == AUTHENTICATION_TYPE[0]:
                args['authMethod']['method'] = gym_login_pw_authenticator.generate_ha1(args['email'],
                                                                                       args['authMethod']['method'])
            return args

        parser = reqparse.RequestParser()
        new_id = db.gym.insert_one(validate_gym_entry_data_for_creation()).inserted_id
        new_gym = db.gym.find_one({'_id': ObjectId(new_id)})
        issued_time = time_tools.get_current_time_second()
        claims = {'iat': issued_time, 'id': str(new_gym['_id']),
                  'type': CLIENT_TYPE["gym"]}
        jwt_token = str(jwt.encode(claims=claims, key=current_app.secret_key, algorithm='HS512'))
        return json.loads(str(Response(success=True, data={'jwt': jwt_token, 'gym': sanitize_gym_return_data(new_gym)}))), 201

    @gym_auth.login_required
    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('announcement_ids', location='args', type=str)
        parser.add_argument('Authorization', trim=True, type=bearer_header_str, nullable=False, location='headers', required=True, help='Needs to be logged in to delete')
        args = parser.parse_args()
        token = args['Authorization']
        claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS512',
                           options={'verify_exp': False})
        target_id = claim.get('id')
        if args.get('announcement_ids') and len(args.get('announcement_ids')) > 0:
            ids = [{'_id': ObjectId(announcement_id)} for announcement_id in args.get('announcement_ids').split(',')]
            current_app.logger.debug(ids)
            remove_announcements_query = {'$pull': {'announcements': {'$or': ids}}}
            result = db.gym.update_one(filter={"_id": ObjectId(target_id)}, update=remove_announcements_query)
            if result.modified_count > 0:
                result = db.gym.find_one({"_id": ObjectId(target_id)})
                return json.loads(str(Response(success=True, data=sanitize_gym_return_data(result)))), 200
            else:
                return json.loads(str(Response(success=True))), 304
        else:
            return json.loads(str(Response(success=True))), 304


def validate_announcement_entry_data(data=None):
    if data is None:
        raise exception.InvalidRequestError('announcement')
    if data.get('title') is None:
        raise exception.InvalidResourceStructureError('title', 'announcement')
    if (data.get('content') is None or data.get('content') == "") and (
                    data.get('imageURLs') is None or data.get('imageURLs').__len__() == 0):
        raise exception.InvalidResourceStructureError('content', 'announcement')
    if data.get('scope') is None or data.get('scope') > 2 or data.get('scope') < 1:
        raise exception.InvalidResourceStructureError('scope', 'announcement')
    if data.get('actionType') is not None and data.get('actionType') != "":
        if data.get('actionType').get('type') is None or data.get('actionType').get('type') == "":
            raise exception.InvalidResourceStructureError('actionType', 'announcement')
        if data.get('actionType').get('content') is None or data.get('actionType').get('type') == "":
            raise exception.InvalidResourceStructureError('actionType', 'announcement')
    data['_id'] = ObjectId()
    data['createdDate'] = time_tools.get_current_time()
    return data


def validate_privilege_for_gym():
    auth_type, token = request.headers['Authorization'].split(None, 1)
    claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS512',
                       options={'verify_exp': False})
    gym_id = claim.get('id')
    request_gym = db.gym.find_one(filter={"_id": ObjectId(gym_id)})
    if request_gym is None:
        raise exception.AttemptedToAccessRestrictedResourceError("Gym")
    return gym_id


class Sync(Resource):

    @gym_auth.login_required
    def get(self):
        target_id = validate_privilege_for_gym()
        gym = db.gym.find_one({'_id': ObjectId(target_id)})
        merchandises = []
        raw_results = db.merchandise.find(filter={'owner': ObjectId(target_id)}, limit=20).sort('announcements.createdDate', ASCENDING)
        for result in raw_results:
            merchandises.append(sanitize_merchandise_return_data(result))
        return Response(success=True,
                        data={'gym': sanitize_gym_return_data(gym), 'merchandises': merchandises}).__dict__, 200

merchandise_api = Blueprint("merchandise_api", __name__, url_prefix='/api/merchandise')
merchandise_api_router = Api(merchandise_api)
merchandise_api_router.add_resource(Merchandise, '/')

gym_api = Blueprint("gym_api", __name__, url_prefix='/api/gym')
gym_api_router = Api(gym_api)
gym_api_router.add_resource(Gym, '/')
gym_api_router.add_resource(Sync, '/sync')
