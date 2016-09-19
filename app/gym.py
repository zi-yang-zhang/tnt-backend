from jose import jwt

from authenticator import user_auth
from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import request, current_app
from flask_restful import Resource
import utils
from database import gym_db as db
import json

from basic_response import InvalidResourceStructureError, InvalidResourceParameterError, InvalidOperationError, \
    InvalidRequestError, DuplicateResourceCreationError, InvalidIdUpdateRequestError,  \
    AttemptedToAccessRestrictedResourceError, Response, ErrorResponse, NotSupportedOperationError


class Merchandise(Resource):

    def get(self, obj_id):
        try:
            result = db.merchandise.find_one({"_id": ObjectId(obj_id)})
        except TypeError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidId as e:
            return json.loads(str(ErrorResponse(e))), 400
        if result is None:
            return json.loads(str(Response(False, ""))), 404
        return json.loads(str(Response(True, sanitize_merchandise_return_data(result))))

    # @user_auth.login_required
    def post(self):
        try:
            args = request.get_json()
            if args is None:
                raise InvalidRequestError('payload')
            operation = args.get('operation')
            data = args.get('data')
            current_app.logger.info('Merchandise request received %s', args)

            if operation is None:
                raise InvalidRequestError('operation')
            if operation == 'create':
                new_id = db.merchandise.insert_one(validate_merchandise_entry_data_for_creation(data)).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id)))), 201
            elif operation == 'update':
                if data.get('_id') is None:
                    raise InvalidIdUpdateRequestError('Merchandise', data.get('_id'))
                id_to_update = data.get('_id')
                validate_gym_privilege_for_merchandise(id_to_update)
                update_query = generate_update_merchandise_command(data)
                result = db.merchandise.update_one({"_id": ObjectId(id_to_update)}, update_query)
                if result.matched_count == 0:
                    raise InvalidIdUpdateRequestError('Merchandise', data.get('_id'))
                return json.loads(str(Response(success=True, data=str(result.upserted_id))))
            elif operation == 'query':
                keyword_field = data.get('keyword')
                owner_field = data.get('owner')
                limit = data.get('find')
                results = []
                if limit is None:
                    limit = 0
                if keyword_field is not None:
                    subquery = []
                    for keyword in keyword_field:
                        subquery.append({"name": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                        subquery.append({"tag": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                        subquery.append({"detail": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                        subquery.append({"summary": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                    criteria = {"$or": subquery}
                    raw_results = db.merchandise.find(filter=criteria, limit=limit)
                    for result in raw_results:
                        results.append(sanitize_merchandise_return_data(result))
                elif owner_field is not None:
                    criteria = {"owner": ObjectId(owner_field)}
                    raw_results = db.merchandise.find(filter=criteria, limit=limit)
                    for result in raw_results:
                        results.append(sanitize_merchandise_return_data(result))
                current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
                if len(results) == 0:
                    return json.loads(str(Response(success=False, data=results))), 404
                else:
                    return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)

        except TypeError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidId as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidIdUpdateRequestError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except AttemptedToAccessRestrictedResourceError as e:
            return json.loads(str(ErrorResponse(e))), 401

    @user_auth.login_required
    def delete(self, obj_id):
        try:
            validate_gym_privilege_for_merchandise(obj_id)
            result = db.merchandise.delete_one({"_id": ObjectId(obj_id)})
            if result.deleted_count < 1:
                return json.loads(str(Response(False, result.deleted_count))), 404
            return json.loads(str(Response(True, result.deleted_count)))
        except AttemptedToAccessRestrictedResourceError as e:
            return json.loads(str(ErrorResponse(e))), 401


def validate_create_gym_entry_data(data=None):
    if data is None:
        raise InvalidRequestError('data')
    if data.get('email') is None or data.get('email') == "":
        raise InvalidResourceStructureError('email', 'Gym')
    if data.get('password') is None or data.get('password') == "":
        raise InvalidResourceStructureError('password', 'Gym')
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'Gym')
    if data.get('address') is None or data.get('address') == "":
        raise InvalidResourceStructureError('address', 'Gym')
    if data.get('geoLocation') is None or data.get('geoLocation') == "":
        raise InvalidResourceStructureError('geoLocation', 'Gym')

    duplicate_check_query = db.gym.find_one(filter={"email": data.get('email')})
    if duplicate_check_query is not None:
        raise DuplicateResourceCreationError(data.get('email'), 'Gym')
    return data


def validate_announcement_entry_data(data=None):
    if data is None:
        raise InvalidRequestError('announcement')
    if (data.get('content') is None or data.get('content') == "") and (data.get('imageURLs') is None or data.get('imageURLs').__len__() == 0):
        raise InvalidResourceStructureError('content', 'announcement')
    if data.get('scope') is None or data.get('scope') > 2 or data.get('scope') < 1:
        raise InvalidResourceStructureError('scope', 'announcement')
    if data.get('actionType') is not None and data.get('actionType') != "":
        if data.get('actionType').get('type') is None or data.get('actionType').get('type') == "":
            raise InvalidResourceStructureError('actionType', 'announcement')
        if data.get('actionType').get('content') is None or data.get('actionType').get('type') == "":
            raise InvalidResourceStructureError('actionType', 'announcement')
    return data


def validate_merchandise_entry_data_for_creation(data=None):
    if data is None:
        raise InvalidRequestError('data')
    if data.get('type') is None or data.get('type') > 2 or data.get('type') < 1:
        raise InvalidResourceStructureError('type', 'Merchandise')
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'Merchandise')
    if data.get('detail') is None or data.get('detail') == "":
        raise InvalidResourceStructureError('detail', 'Merchandise')
    if data.get('owner') is None or data.get('owner') == "":
        raise InvalidResourceStructureError('owner', 'Merchandise')
    else:
        gym_id = data.get('owner')
        owner = db.gym.find_one({"_id": ObjectId(gym_id)})
        if owner is None:
            raise InvalidResourceParameterError('owner', 'Merchandise')
        else:
            data.update({'owner': owner.get("_id")})
    if data.get('price') is None or data.get('price') == "":
        data.update({'price': {'amount': 0, 'currency': "CNY"}})

    return data


def generate_update_merchandise_command(data=None):
    command = {}
    set_target = {}
    if data is None:
        raise InvalidRequestError('data')
    if data.get('type') is not None:
        if data.get('type') > 2 or data.get('type') < 1:
            raise InvalidResourceStructureError('type', 'Merchandise')
        else:
            set_target['type'] = data.get('type')
    if data.get('name') is not None:
        if data.get('name') == "":
            raise InvalidResourceStructureError('name', 'Merchandise')
        else:
            set_target['name'] = data.get('name')
    if data.get('detail') is not None:
        if data.get('detail') == "":
            raise InvalidResourceStructureError('detail', 'Merchandise')
        else:
            set_target['detail'] = data.get('detail')
    if data.get('owner') is not None:
        if data.get('owner') == "":
            raise InvalidResourceStructureError('owner', 'Merchandise')
        else:
            gym_id = data.get('owner')
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
    if data.get('price') is not None and data.get('price') == "":
        set_target['price'] = {'amount': 0, 'currency': "CNY"}
    if data.get('count') is not None:
        set_target['count'] = data.get('count')
    if data.get('summary') is not None:
        set_target['summary'] = data.get('summary')
    if data.get('tag') is not None:
        set_target['tag'] = data.get('tag')
    if data.get('expiryInfo') is not None:
        set_target['expiryInfo'] = data.get('expiryInfo')
    command['$set'] = set_target

    if data.get('schedule') is not None:
        if not isinstance(data.get('schedule'), list):
            raise InvalidResourceParameterError('schedule', 'Merchandise')
        elif len(data.get('schedule')) > 0:
            if '$push' not in command:
                command['$push'] = {}
            command['$push']['schedule'] = {'$each': data.get('schedule')}

    if data.get('imageURLs') is not None:
        if not isinstance(data.get('imageURLs'), list):
            raise InvalidResourceParameterError('imageURLs', 'Merchandise')
        elif len(data.get('imageURLs')) > 0:
            if '$push' not in command:
                command['$push'] = {}
            command['$push']['imageURLs'] = {'$each': data.get('imageURLs')}
    return command


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
        del data['password']
        data.update({'geoLocation': data.get('geoLocation').get('coordinates')})
    return data


def validate_gym_privilege_for_merchandise(merchandise_id):
    auth_type, token = request.headers['Authorization'].split(
        None, 1)
    claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256', options={'verify_exp': False})
    gym_email = claim.get('user')
    gym = db.gym.find_one(filter={"email": gym_email})
    merchandise = db.merchandise.find_one(filter={"_id": ObjectId(merchandise_id)})
    if gym is None:
        raise AttemptedToAccessRestrictedResourceError("Merchandise")
    elif merchandise is not None and ObjectId(merchandise.get('owner')) != gym.get('_id'):
        raise AttemptedToAccessRestrictedResourceError("Merchandise")


class Gym(Resource):

    def get(self, obj_id):
        try:
            result = db.gym.find_one({"_id": ObjectId(obj_id)})
        except TypeError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidId as e:
            return json.loads(str(ErrorResponse(e))), 400
        if result is None:
            return json.loads(str(Response(False, ""))), 404
        return json.loads(str(Response(True, sanitize_gym_return_data(utils.bson_to_json(result)))))

    def post(self):
        try:
            args = request.get_json()
            if args is None:
                raise InvalidRequestError('payload')
            operation = args.get('operation')
            data = args.get('data')
            current_app.logger.info('Gym request received %s', args)
            if operation is None:
                raise InvalidRequestError('operation')
            if operation == 'create':
                new_id = db.gym.insert_one(validate_gym_entry_data_for_creation(data)).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id)))), 201
            elif operation == 'update':
                if data.get('_id') is None:
                    raise InvalidIdUpdateRequestError('Gym', data.get('_id'))
                id_to_update = data.get('_id')
                validate_privilege_for_gym(id_to_update)
                update_query = generate_update_gym_command(data)
                result = db.gym.update_one({"_id": ObjectId(id_to_update)}, update_query)
                if result.matched_count == 0:
                    raise InvalidIdUpdateRequestError('Merchandise', data.get('_id'))
                return json.loads(str(Response(success=True, data=str(result.upserted_id))))
            elif operation == 'query':
                limit = data.get('find')
                results = []
                if data.get('email') is not None:
                    raw_result = db.gym.find_one({'email': data.get('email')})
                    if raw_result is not None:
                        results.append(sanitize_gym_return_data(raw_result))
                elif data.get('address') is not None:
                    address_field = data.get('address')
                    criteria = {"address": {"$regex": ".*{}.*".format(address_field.encode('utf-8'))}}
                    raw_results = db.gym.find(filter=criteria, limit=limit)
                    for result in raw_results:
                        results.append(sanitize_gym_return_data(result))
                elif data.get('near') is not None:
                    near_field = data.get('near')
                    if near_field.get('coordinates') is None or near_field.get('coordinates') == "" or not isinstance(near_field.get('coordinates'), list) or len(near_field.get('coordinates')) < 2 or len(near_field.get('coordinates')) > 2:
                        raise InvalidResourceStructureError('coordinates', 'near')
                    else:
                        command = {}
                        near_target = {}
                        coordinates = near_field.get('coordinates')
                        near_target['$geometry'] = {'type': "Point", 'coordinates': coordinates}
                        if near_field.get('max') is not None:
                            near_target['$maxDistance'] = near_field.get('max')
                        if near_field.get('min') is not None:
                            near_target['$minDistance'] = near_field.get('min')
                        command['$near'] = near_target
                        raw_results = db.gym.find(filter={"geoLocation": command}, limit=limit)
                        for result in raw_results:
                            results.append(sanitize_gym_return_data(result))
                        current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
                        if len(results) == 0:
                            return json.loads(str(Response(success=False, data=results))), 404
                        else:
                            return json.loads(str(Response(success=True, data=results)))
                elif data.get('keyword') is not None:
                    keyword_field = data.get('keyword')
                    subquery = []
                    for keyword in keyword_field:
                        subquery.append({"name": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                        subquery.append({"address": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                        subquery.append({"detail": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                    criteria = {"$or": subquery}
                    raw_results = db.gym.find(filter=criteria, limit=limit)
                    for result in raw_results:
                        results.append(sanitize_gym_return_data(result))
                current_app.logger.info('response sent %s', str(Response(success=True, data=results)))
                if len(results) == 0:
                    return json.loads(str(Response(success=False, data=results))), 404
                else:
                    return json.loads(str(Response(success=True, data=results)))
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except InvalidIdUpdateRequestError as e:
            return json.loads(str(ErrorResponse(e))), 400
        except AttemptedToAccessRestrictedResourceError as e:
            return json.loads(str(ErrorResponse(e))), 401


def validate_gym_entry_data_for_creation(data=None):
    if data is None:
        raise InvalidRequestError('data')
    if data.get('email') is None or data.get('email') == "":
        raise InvalidResourceStructureError('email', 'Gym')
    if data.get('password') is None or data.get('password') == "":
        raise InvalidResourceStructureError('password', 'Gym')
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'Gym')
    if data.get('address') is None or data.get('address') == "":
        raise InvalidResourceStructureError('address', 'Gym')
    if data.get('geoLocation') is None or data.get('geoLocation') == "" or not isinstance(data.get('geoLocation'), list):
        raise InvalidResourceStructureError('geoLocation', 'Gym')
    elif len(data.get('geoLocation')) != 2:
        raise InvalidResourceStructureError('geoLocation', 'Gym')
    else:
        coordinates = data.get('geoLocation')
        data.update({'geoLocation': {'type': "Point", 'coordinates': coordinates}})
    duplicate = db.gym.find_one({"email": data.get('email')})
    if duplicate is not None:
        raise DuplicateResourceCreationError('email', 'Gym')
    return data


def generate_update_gym_command(data=None):
    command = {}
    set_target = {}
    if data is None:
        raise InvalidRequestError('data')
    if data.get('email') is not None:
        if data.get('email') == "":
            raise InvalidResourceStructureError('email', 'Gym')
        else:
            set_target['email'] = data.get('email')
    if data.get('password') is not None:
        raise NotSupportedOperationError('update password', 'Gym')
    if data.get('name') is not None:
        if data.get('name') == "":
            raise InvalidResourceStructureError('name', 'Gym')
        else:
            set_target['name'] = data.get('name')
    if data.get('address') is not None:
        if data.get('address') == "":
            raise InvalidResourceStructureError('address', 'Gym')
        else:
            set_target['address'] = data.get('address')
    if data.get('geoLocation') is not None:
        if data.get('geoLocation') == "":
            raise InvalidResourceStructureError('geoLocation', 'Gym')
        else:
            set_target['geoLocation'] = data.get('geoLocation')
    if data.get('smallLogo') is not None:
        set_target['smallLogo'] = data.get('smallLogo')
    if data.get('bigLogo') is not None:
        set_target['bigLogo'] = data.get('bigLogo')
    if data.get('detail') is not None:
        set_target['detail'] = data.get('detail')
    command['$set'] = set_target

    if data.get('service') is not None:
        if not isinstance(data.get('service'), list):
            raise InvalidResourceParameterError('service', 'Gym')
        elif len(data.get('service')) > 0:
            if '$push' not in command:
                command['$push'] = {}
            command['$push']['service'] = {'$each': data.get('service')}

    if data.get('announcements') is not None:
        validate_announcement_entry_data(data.get('announcements'))
        if '$push' not in command:
            command['$push'] = {}
        command['$push']['announcements'] = data.get('announcements')

    return command


def validate_privilege_for_gym(gym_id):
    auth_type, token = request.headers['Authorization'].split(None, 1)
    claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256', options={'verify_exp': False})
    gym_email = claim.get('user')
    request_gym = db.gym.find_one(filter={"email": gym_email})

    if request_gym is None:
        raise AttemptedToAccessRestrictedResourceError("Gym")
    elif request_gym.get('_id') != ObjectId(gym_id):
        raise AttemptedToAccessRestrictedResourceError("Gym")
