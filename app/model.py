import json
import logging

import utils
from authenticator import resource_auth
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import request
from flask_restful import Resource

from database import resource as db

LOGGER = logging.getLogger()


class InvalidResourceCreationError(Exception):
    def __init__(self, param, resource_type):
        self.message = param + " is required for creating " + resource_type


class InvalidResourceParameterError(Exception):
    def __init__(self, param, resource_type):
        self.message = param + " cannot be found in " + resource_type


class InvalidOperationError(Exception):
    def __init__(self, param):
        self.message = "Operation " + param + " is not supported"


class InvalidRequestError(Exception):
    def __init__(self, param):
        self.message = param + " is required for the request"


class DuplicateResourceCreationError(Exception):
    def __init__(self, name, resource_type):
        self.message = "Resource exists with name <" + name + "> for " + resource_type


class Response(object):
    def __init__(self, success, data=None):
        if data is None:
            self.data = {}
        else:
            self.data = data
        self.success = success

    def set_data(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.__dict__)


class ErrorResponse(Response):
    def __init__(self, exception):
        super(ErrorResponse, self).__init__(success=False)
        self.exception_message = exception.message


class EquipmentType(Resource):

    @resource_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        data = args['data']
        try:
            if operation == 'create':
                if data.get('name') is None:
                    raise InvalidResourceCreationError('name', 'EquipmentType')
                duplicate_check_query = db.equipment_type.find_one(filter={"name": data.get('name')})
                if duplicate_check_query is not None:
                    raise DuplicateResourceCreationError(data.get('name'), 'EquipmentType')
                new_id = db.equipment_type.insert_one(data).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                raise NotImplementedError
            elif operation == 'query':
                name_field = data.get('name')
                limit = data.get('find')
                if limit is None:
                    limit = 0
                criteria = {}
                if name_field is not None:
                    criteria = {"name": utils.translate_query(name_field)}
                results = []
                for result in db.equipment_type.find(filter=criteria, limit=limit):
                    results.append(utils.bson_to_json(result))
                return json.loads(str(Response(success=True, data=results)))
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))

    @resource_auth.login_required
    def get(self, obj_id):
        result = db.equipment_type.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_auth.login_required
    def delete(self, obj_id):
        result = db.equipment_type.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result


class Equipment(Resource):

    @resource_auth.login_required
    def delete(self, obj_id):
        result = db.equipment.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result

    @resource_auth.login_required
    def get(self, obj_id):
        result = db.equipment.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(json.loads(dumps(result)))

    @resource_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        data = args['data']
        LOGGER.debug('Equipment request received %s', args)
        try:
            if operation == 'create':
                equipment_type = data.get('type')
                detail = data.get('detail')
                images = data.get('imageURLs')
                if data.get('name') is None:
                    raise InvalidResourceCreationError('name', 'Equipment')
                if equipment_type is None:
                    raise InvalidResourceCreationError('equipment_type', 'Equipment')
                if detail is None:
                    data.update({"detail": ""})
                if images is None:
                    data.update({"imageURLs": []})
                duplicate_check_query = db.equipment.find_one(filter={"name": data.get('name')})
                if duplicate_check_query is not None:
                    raise DuplicateResourceCreationError(data.get('name'), 'Equipment')
                type_result = db.equipment_type.find_one({"name": equipment_type})
                if type_result is not None:
                    data['type'] = type_result['_id']
                else:
                    data['type'] = db.equipment_type.insert_one({"name": equipment_type}).inserted_id
                new_equipment = db.equipment.insert_one(data)
                LOGGER.debug(new_equipment)
                new_id = new_equipment.inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                raise NotImplementedError
            elif operation == 'query':
                name_field = data.get('name')
                type_field = data.get('type')
                limit = data.get('find')
                if limit is None:
                    limit = 0
                criteria = {}
                if name_field is not None and type_field is not None:
                    type_results = db.equipment_type.find(filter={"name": utils.translate_query(type_field)})
                    and_criteria = [{"name": utils.translate_query(name_field)}]
                    type_criteria = []
                    for type_result in type_results:
                        type_criteria.append({"type": utils.bson_to_json(type_result)['_id']})
                    if type_criteria.__len__() > 0:
                        and_criteria.append({"$or": type_criteria})
                    criteria = {"$and": and_criteria}
                elif name_field is not None:
                    criteria = {"name": utils.translate_query(name_field)}
                elif type_field is not None:
                    type_results = db.equipment_type.find(filter={"name": utils.translate_query(type_field)})
                    if type_results.count() == 0:
                        return []
                    type_criteria = []
                    for type_result in type_results:
                        type_criteria.append({"type": type_result['_id']})
                    if type_criteria.__len__() > 0:
                        criteria = {"$or": type_criteria}
                results = []
                for raw_result in db.equipment.find(filter=criteria, limit=limit):
                    result = utils.bson_to_json(raw_result)
                    equipment_type_id = raw_result['type']
                    equipment_type = db.equipment_type.find_one(filter={"_id": equipment_type_id})
                    del result['type']
                    result.update({'type': utils.bson_to_json(equipment_type)})
                    results.append(result)
                LOGGER.debug('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))


class Muscle(Resource):

    @resource_auth.login_required
    def delete(self, obj_id):
        result = db.muscle.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result

    @resource_auth.login_required
    def get(self, obj_id):
        result = db.muscle.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(json.loads(dumps(result)))

    @resource_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        data = args['data']
        LOGGER.debug('Muscle request received %s', args)
        try:
            if operation == 'create':
                if data.get('name') is None:
                    raise InvalidResourceCreationError('name', 'Muscle')
                if data.get('imageURLs') is None:
                    data.update({'imageURLs': []})
                duplicate_check_query = db.muscle.find_one(filter={"name": data.get('name')})
                if duplicate_check_query is not None:
                    raise DuplicateResourceCreationError(data.get('name'), 'Muscle')
                new_id = db.muscle.insert_one(data).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                raise NotImplementedError
            elif operation == 'query':
                name_field = data.get('name')
                limit = data.get('find')
                if limit is None:
                    limit = 0
                criteria = {}
                if name_field is not None:
                    criteria = {"name": utils.translate_query(name_field)}
                results = []
                for result in db.muscle.find(filter=criteria, limit=limit):
                    results.append(utils.bson_to_json(result))
                LOGGER.debug('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))


class MuscleGroup(Resource):

    @resource_auth.login_required
    def delete(self, obj_id):
        result = db.muscle_group.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result

    @resource_auth.login_required
    def get(self, obj_id):
        result = db.muscle_group.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(json.loads(dumps(result)))

    @resource_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        data = args['data']
        LOGGER.debug('MuscleGroup request received %s', args)
        try:
            if operation == 'create':
                if data.get('name') is None:
                    raise InvalidResourceCreationError('name', 'MuscleGroup')
                if data.get('muscles') is None or data.get('muscles').__len__() < 1:
                    raise InvalidResourceCreationError('muscles', 'MuscleGroup')
                if data.get('imageURLs') is None:
                    data.update({'imageURLs': []})
                duplicate_check_query = db.muscle_group.find_one(filter={"name": data.get('name')})
                if duplicate_check_query is not None:
                    raise DuplicateResourceCreationError(data.get('name'), 'MuscleGroup')
                muscles = data['muscles']
                muscle_ids_to_save = []
                for muscle in muscles:
                    muscle_query = db.muscle.find_one(filter={"name": muscle})
                    if muscle_query is not None:
                        muscle_ids_to_save.append(muscle_query['_id'])
                    else:
                        new_muscle = {"name": muscle, "imageURLs": []}
                        muscle_ids_to_save.append(db.muscle.insert_one(new_muscle).inserted_id)
                data['muscles'] = muscle_ids_to_save
                new_id = db.muscle_group.insert_one(data).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                raise NotImplementedError
            elif operation == 'query':
                name_field = data.get('name')
                muscles_field = data.get('muscles')
                limit = data.get('find')
                if limit is None:
                    limit = 0
                criteria = {}
                if name_field is not None:
                    criteria = {"name": utils.translate_query(name_field)}
                elif muscles_field is not None:
                    muscles_id_list = []
                    muscles_result = []
                    for muscle in muscles_field:
                        muscle_result = db.muscle.find_one(filter={"name": muscle})
                        if muscle_result is None:
                            return []
                        else:
                            muscles_id_list.append(muscle_result['_id'])
                            muscles_result.append(muscle_result)
                    criteria = {"muscles": {"$all": muscles_id_list}}
                results = []
                for raw_result in db.muscle_group.find(filter=criteria, limit=limit):
                    muscles = get_muscles_for_result(raw_result, 'muscles')
                    result = utils.bson_to_json(raw_result)
                    del result['muscles']
                    result.update({'muscles': muscles})
                    results.append(result)
                LOGGER.debug('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))


class ExerciseMetric(Resource):

    @resource_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        data = args['data']

        if operation == 'create':
            try:
                if data.get('name') is None:
                    raise InvalidResourceCreationError('name', 'ExerciseMetric')
                if data.get('unit') is None:
                    raise InvalidResourceCreationError('unit', 'ExerciseMetric')
                if data.get('dataType') is None:
                    raise InvalidResourceCreationError('dataType', 'ExerciseMetric')
                new_id = db.exercise_metric.insert_one(data).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            except InvalidResourceCreationError as e:
                return json.loads(str(ErrorResponse(e)))

        elif operation == 'update':
            raise NotImplementedError
        elif operation == 'query':
            name_field = data.get('name')
            limit = data.get('find')
            if limit is None:
                limit = 0
            criteria = {}
            if name_field is not None:
                criteria = {"name": utils.translate_query(name_field)}
            results = []
            for result in db.exercise_metric.find(filter=criteria, limit=limit):
                results.append(utils.bson_to_json(result))
            return json.loads(str(Response(success=True, data=results)))

    @resource_auth.login_required
    def get(self, obj_id):
        result = db.exercise_metric.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_auth.login_required
    def delete(self, obj_id):
        result = db.exercise_metric.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result


class CategoryTag(Resource):

    @resource_auth.login_required
    def post(self):
        try:
            args = request.get_json()
            operation = args.get('operation')
            data = args.get('data')
            if operation is None:
                raise InvalidRequestError('operation')
            if data is None:
                raise InvalidRequestError('data')
            if operation == 'create':
                if data.get('name') is None:
                    raise InvalidResourceCreationError('name', 'CategoryTag')
                new_id = db.category_type.insert_one(data).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))

            elif operation == 'update':
                raise NotImplementedError
            elif operation == 'query':
                name_field = data.get('name')
                limit = data.get('find')
                if limit is None:
                    limit = 0
                criteria = {}
                if name_field is not None:
                    criteria = {"name": utils.translate_query(name_field)}
                results = []
                for result in db.category_type.find(filter=criteria, limit=limit):
                    results.append(utils.bson_to_json(result))
                return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)

        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))

    @resource_auth.login_required
    def get(self, obj_id):
        result = db.category_type.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_auth.login_required
    def delete(self, obj_id):
        result = db.category_type.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result


class Exercise(Resource):

    @resource_auth.login_required
    def post(self):
        try:
            args = request.get_json()
            operation = args.get('operation')
            data = args.get('data')
            LOGGER.debug('Exercise request received %s', args)

            if operation is None:
                raise InvalidRequestError('operation')
            if data is None:
                raise InvalidRequestError('data')
            if operation == 'create':
                if data.get('name') is None:
                    raise InvalidResourceCreationError('name', 'Exercise')
                if data.get('majorMuscles') is None or data.get('majorMuscles').__len__ == 0:
                    raise InvalidResourceCreationError('majorMuscle', 'Exercise')
                if data.get('repetition') is None and data.get('duration') is None:
                    raise InvalidResourceCreationError('Either repetition or duration', 'Exercise')
                if data.get('repetition') is not None and data.get('duration') is not None:
                    raise InvalidResourceCreationError('Only one of repetition or duration', 'Exercise')

                if data.get('repetition') is None:
                    data.update({'repetition': -1})
                if data.get('duration') is None:
                    data.update({'duration': -1})
                if data.get('count') is None:
                    data.update({'count': 0})

                if data.get('equipments') is None:
                    data.update({'equipments': []})
                else:
                    equipments = data['equipments']
                    equipment_ids_to_save = []
                    for equipment in equipments:
                        equipment_query = db.equipment.find_one(filter={"name": equipment})
                        if equipment_query is not None:
                            equipment_ids_to_save.append(equipment_query['_id'])
                        else:
                            raise InvalidResourceParameterError(equipment, "Equipment")
                    data['equipments'] = equipment_ids_to_save

                if data.get('metrics') is None:
                    data.update({'metrics': []})

                if data.get('resourceURLs') is None:
                    data.update({'resourceURLs': []})

                if data.get('minorMuscles') is None:
                    data.update({'minorMuscles': []})
                else:
                    muscles = data['minorMuscles']
                    muscle_ids_to_save = []
                    for muscle in muscles:
                        muscle_query = db.muscle.find_one(filter={"name": muscle})
                        if muscle_query is not None:
                            muscle_ids_to_save.append(muscle_query['_id'])
                        else:
                            raise InvalidResourceParameterError(muscle, "Muscle")
                    data['minorMuscles'] = muscle_ids_to_save

                if data.get('categoryTags') is None:
                    data.update({'categoryTags': []})

                if data.get('type') is None:
                    data.update({'type': ""})
                if data.get('advancedContent') is None:
                    data.update({'advancedContent': ""})
                if data.get('basicContent') is None:
                    data.update({'basicContent': ""})

                duplicate_check_query = db.exercise.find_one(filter={"name": data.get('name')})
                if duplicate_check_query is not None:
                    raise DuplicateResourceCreationError(data.get('name'), 'Exercise')

                muscles = data['majorMuscles']
                muscle_ids_to_save = []
                for muscle in muscles:
                    muscle_query = db.muscle.find_one(filter={"name": muscle})
                    if muscle_query is not None:
                        muscle_ids_to_save.append(muscle_query['_id'])
                    else:
                        raise InvalidResourceParameterError(muscle, "Muscle")
                data['majorMuscles'] = muscle_ids_to_save
                new_id = db.exercise.insert_one(data).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))

            elif operation == 'update':
                raise NotImplementedError
            elif operation == 'query':
                keyword_field = data.get('keyword')
                limit = data.get('find')
                results = []
                if limit is None:
                    limit = 0
                if keyword_field is not None:
                    subquery = []
                    for keyword in keyword_field:
                        subquery.append({"name": {"$regex": ".*{}.*".format(keyword.encode('utf-8'))}})
                    muscle_result = db.muscle.find(filter={"$or": subquery}, projection={"_id": 1})
                    equipment_result = db.equipment.find(filter={"$or": subquery}, projection={"_id": 1})
                    for muscle_id in muscle_result:
                        subquery.append({"majorMuscles": muscle_id.get("_id")})
                    for equipment_id in equipment_result:
                        subquery.append({"equipments": equipment_id.get("_id")})
                    criteria = {"$or": subquery}
                    for raw_result in db.exercise.find(filter=criteria, limit=limit):
                        major_muscles = get_muscles_for_result(raw_result, "majorMuscles")
                        minor_muscles = get_muscles_for_result(raw_result, "minorMuscles")
                        equipments = get_equipments_for_result(raw_result, "equipments")
                        result = utils.bson_to_json(raw_result)
                        del result["equipments"]
                        result.update({"equipments": equipments})
                        del result["minorMuscles"]
                        result.update({"minorMuscles": minor_muscles})
                        del result["majorMuscles"]
                        result.update({"majorMuscles": major_muscles})
                        results.append(result)
                    LOGGER.debug('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)

        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))

    @resource_auth.login_required
    def get(self, obj_id):
        result = db.exercise.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_auth.login_required
    def delete(self, obj_id):
        result = db.exercise.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result


def get_muscles_for_result(raw_result, param_name):
    muscles = []
    for muscle_id in raw_result[param_name]:
        muscles.append(utils.bson_to_json(db.muscle.find_one(filter={"_id": muscle_id})))
    return muscles


def get_equipments_for_result(raw_result, param_name):
    equipments = []
    for equipment_id in raw_result[param_name]:
        equipments.append(utils.bson_to_json(db.equipment.find_one(filter={"_id": equipment_id})))
    return equipments
