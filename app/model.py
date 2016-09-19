# coding=utf-8
import datetime
import json
import logging

from basic_response import InvalidResourceStructureError, InvalidResourceParameterError, InvalidOperationError, \
    InvalidRequestError, DuplicateResourceCreationError, InvalidIdUpdateRequestError, AttemptedToDeleteInUsedResource, \
    AttemptedToAccessRestrictedResourceError, Response, ErrorResponse
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import request, current_app
from flask_restful import Resource
from jose import jwt

import utils
from authenticator import resource_access_auth, user_auth
from database import resource_db as db

LOGGER = logging.getLogger()

PRIVILEGE_GROUP = {0: {'r': 'all',
                       'c': 'all',
                       'u': 'all',
                       'd': 'all'},
                   1: {'r': 'all',
                       'c': 'all',
                       'u': 'all',
                       'd': 'all'},
                   2: {'r': 'all',
                       'c': 'all',
                       'u': 'all',
                       'd': 'all'},
                   3: {'r': 'all',
                       'c': ['Exercise', 'TrainingPlan', 'Equipment']},
                   4: {'r': 'all'},
                   5: None
                   }


class EquipmentType(Resource):

    @resource_access_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        data = args['data']
        validate_user_privilege(operation=operation, resource_type='EquipmentType')
        try:
            if operation == 'create':
                if data.get('name') is None:
                    raise InvalidResourceStructureError('name', 'EquipmentType')
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
            else:
                raise InvalidOperationError(operation)
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))

    @resource_access_auth.login_required
    def get(self, obj_id):
        result = db.equipment_type.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_access_auth.login_required
    def delete(self, obj_id):
        result = db.equipment_type.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result


class Equipment(Resource):

    @resource_access_auth.login_required
    def delete(self, obj_id):
        in_use_query_exercise = {"equipments": {'$elemMatch': {'$eq': ObjectId(obj_id)}}}
        in_use_query_exercise_result = db.exercise.find(in_use_query_exercise, projection={"name": 1, "_id": 0})
        if in_use_query_exercise_result.count() == 0:
            result = db.equipment.delete_one({"_id": ObjectId(obj_id)})
            return json.loads(str(Response(success=True))) if result.deleted_count > 0 else json.loads(
                str(Response(success=False)))
        else:
            result_name_list = []
            for result in in_use_query_exercise_result:
                result_name_list.append(result.get('name'))
            target_to_be_deleted = db.equipment.find_one({'_id': ObjectId(obj_id)}, projection={"name": 1, "_id": 0})
            return json.loads(
                str(ErrorResponse(AttemptedToDeleteInUsedResource(target_to_be_deleted.get('name'), result_name_list))))

    @resource_access_auth.login_required
    def get(self, obj_id):
        result = db.equipment.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(json.loads(dumps(result)))

    @resource_access_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        validate_user_privilege(operation=operation, resource_type='Equipment')
        data = args['data']
        LOGGER.info('Equipment request received %s', args)
        try:
            if operation == 'create':
                new_id = db.equipment.insert_one(validate_equipment_entry_data(data)).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                if data.get('_id') is None:
                    raise InvalidIdUpdateRequestError('Equipment', data.get('_id'))
                update_query = validate_equipment_entry_data(data, False)
                id_to_update = data.get('_id')
                del update_query['_id']
                update_query = {'$set': update_query}
                result = db.equipment.update_one({"_id": ObjectId(id_to_update)}, update_query)
                if result.matched_count == 0:
                    raise InvalidIdUpdateRequestError('Equipment', data.get('_id'))
                return json.loads(str(Response(success=True, data=str(result.upserted_id))))
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
                LOGGER.info('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidIdUpdateRequestError as e:
            return json.loads(str(ErrorResponse(e)))


class Muscle(Resource):

    @resource_access_auth.login_required
    def delete(self, obj_id):
        in_use_query_muscle_group = {"muscles": {'$elemMatch': {'$eq': ObjectId(obj_id)}}}
        in_use_query_exercise = {'$or': [{"majorMuscles": {'$elemMatch': {'$eq': ObjectId(obj_id)}}}, {"minorMuscles": {'$elemMatch': {'$eq': ObjectId(obj_id)}}}]}

        in_use_query_muscle_group_result = db.muscle_group.find(in_use_query_muscle_group, projection={"name": 1, "_id": 0})
        in_use_query_exercise_result = db.exercise.find(in_use_query_exercise, projection={"name": 1, "_id": 0})

        if in_use_query_muscle_group_result.count() == 0 and in_use_query_exercise_result.count() == 0:
            result = db.muscle.delete_one({"_id": ObjectId(obj_id)})
            return json.loads(str(Response(success=True))) if result.deleted_count > 0 else json.loads(str(
                Response(success=False)))
        else:
            result_name_list = []
            if in_use_query_muscle_group_result.count() > 0:
                for result in in_use_query_muscle_group_result:
                    result_name_list.append(result.get('name'))

            if in_use_query_exercise_result.count() > 0:
                for result in in_use_query_exercise_result:
                    result_name_list.append(result.get('name'))
            target_to_be_deleted = db.muscle.find_one({'_id': ObjectId(obj_id)}, projection={"name": 1, "_id": 0})
            return json.loads(str(
                ErrorResponse(AttemptedToDeleteInUsedResource(target_to_be_deleted.get('name'), result_name_list))))

    @resource_access_auth.login_required
    def get(self, obj_id):
        result = db.muscle.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(json.loads(dumps(result)))

    @resource_access_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        validate_user_privilege(operation=operation, resource_type='Muscle')
        data = args['data']
        LOGGER.info('Muscle request received %s', args)
        try:
            if operation == 'create':
                new_id = db.muscle.insert_one(validate_muscle_entry_data(data)).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                if data.get('_id') is None:
                    raise InvalidIdUpdateRequestError('Muscle', data.get('_id'))
                update_query = validate_muscle_entry_data(data, False)
                id_to_update = data.get('_id')
                del update_query['_id']
                update_query = {'$set': update_query}
                result = db.muscle.update_one({"_id": ObjectId(id_to_update)}, update_query)
                if result.matched_count == 0:
                    raise InvalidIdUpdateRequestError('Muscle', data.get('_id'))
                return json.loads(str(Response(success=True, data=str(result.upserted_id))))
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
                LOGGER.info('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidIdUpdateRequestError as e:
            return json.loads(str(ErrorResponse(e)))


class MuscleGroup(Resource):

    @resource_access_auth.login_required
    def delete(self, obj_id):
        result = db.muscle_group.delete_one({"_id": ObjectId(obj_id)})
        return json.loads(str(Response(success=True))) if result.deleted_count > 0 else json.loads(str(
            Response(success=False)))

    @resource_access_auth.login_required
    def get(self, obj_id):
        result = db.muscle_group.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(json.loads(dumps(result)))

    @resource_access_auth.login_required
    def post(self):
        args = request.get_json()
        operation = args['operation']
        validate_user_privilege(operation=operation, resource_type='MuscleGroup')
        data = args['data']
        LOGGER.info('MuscleGroup request received %s', args)
        try:
            if operation == 'create':
                new_id = db.muscle_group.insert_one(validate_muscle_group_entry_data(data)).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                if data.get('_id') is None:
                    raise InvalidIdUpdateRequestError('MuscleGroup', data.get('_id'))
                update_query = validate_muscle_group_entry_data(data, False)
                id_to_update = data.get('_id')
                del update_query['_id']
                update_query = {'$set': update_query}
                result = db.muscle_group.update_one({"_id": ObjectId(id_to_update)}, update_query)
                if result.matched_count == 0:
                    raise InvalidIdUpdateRequestError('MuscleGroup', data.get('_id'))
                return json.loads(str(Response(success=True, data=str(result.upserted_id))))
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
                LOGGER.info('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)
        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidIdUpdateRequestError as e:
            return json.loads(str(ErrorResponse(e)))


class ExerciseMetric(Resource):

    @resource_access_auth.login_required
    def post(self):
        args = request.get_json()

        operation = args['operation']
        validate_user_privilege(operation=operation, resource_type='ExerciseMetric')
        data = args['data']

        if operation == 'create':
            try:
                if data.get('name') is None:
                    raise InvalidResourceStructureError('name', 'ExerciseMetric')
                if data.get('unit') is None:
                    raise InvalidResourceStructureError('unit', 'ExerciseMetric')
                if data.get('dataType') is None:
                    raise InvalidResourceStructureError('dataType', 'ExerciseMetric')
                new_id = db.exercise_metric.insert_one(data).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            except InvalidResourceStructureError as e:
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

    @resource_access_auth.login_required
    def get(self, obj_id):
        result = db.exercise_metric.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_access_auth.login_required
    def delete(self, obj_id):
        result = db.exercise_metric.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result


class CategoryTag(Resource):

    @resource_access_auth.login_required
    def post(self):
        try:
            args = request.get_json()

            operation = args.get('operation')
            validate_user_privilege(operation=operation, resource_type='CategoryTag')
            data = args.get('data')
            if operation is None:
                raise InvalidRequestError('operation')
            if data is None:
                raise InvalidRequestError('data')
            if operation == 'create':
                if data.get('name') is None:
                    raise InvalidResourceStructureError('name', 'CategoryTag')
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
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))

    @resource_access_auth.login_required
    def get(self, obj_id):
        result = db.category_type.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_access_auth.login_required
    def delete(self, obj_id):
        result = db.category_type.delete_one({"_id": ObjectId(obj_id)})
        return result.raw_result


class Exercise(Resource):

    @resource_access_auth.login_required
    def post(self):
        try:
            args = request.get_json()

            operation = args.get('operation')
            validate_user_privilege(operation=operation, resource_type='Exercise')
            data = args.get('data')
            LOGGER.info('Exercise request received %s', args)

            if operation is None:
                raise InvalidRequestError('operation')
            if data is None:
                raise InvalidRequestError('data')
            if operation == 'create':
                new_id = db.exercise.insert_one(validate_exercise_entry_data(data)).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                if data.get('_id') is None:
                    raise InvalidIdUpdateRequestError('Exercise', data.get('_id'))
                update_query = validate_exercise_entry_data(data, False)
                id_to_update = data.get('_id')
                del update_query['_id']
                update_query = {'$set': update_query}
                result = db.exercise.update_one({"_id": ObjectId(id_to_update)}, update_query)
                if result.matched_count == 0:
                    raise InvalidIdUpdateRequestError('Exercise', data.get('_id'))
                return json.loads(str(Response(success=True, data=str(result.upserted_id))))
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
                        results.append(fetch_data_for_exercise(raw_result))
                    LOGGER.info('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)

        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidIdUpdateRequestError as e:
            return json.loads(str(ErrorResponse(e)))

    @resource_access_auth.login_required
    def get(self, obj_id):
        result = db.exercise.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    @resource_access_auth.login_required
    def delete(self, obj_id):
        result = db.exercise.delete_one({"_id": ObjectId(obj_id)})
        return json.loads(str(Response(success=True))) if result.deleted_count > 0 else json.loads(str(
            Response(success=False)))


class TrainingPlan(Resource):

    @user_auth.login_required
    def get(self, obj_id):
        result = db.exercise.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return json.loads(str(Response(success=True, data=utils.bson_to_json(result))))

    @user_auth.login_required
    def post(self):
        try:
            args = request.get_json()

            operation = args.get('operation')
            validate_user_privilege(operation=operation, resource_type='TrainingPlan')
            data = args.get('data')
            LOGGER.info('TrainingPlan request received %s', args)

            if operation is None:
                raise InvalidRequestError('operation')
            if data is None:
                raise InvalidRequestError('data')
            if operation == 'create':
                new_id = db.training_plan.insert_one(validate_training_plan_entry_data(data)).inserted_id
                return json.loads(str(Response(success=True, data=str(new_id))))
            elif operation == 'update':
                if data.get('_id') is None:
                    raise InvalidIdUpdateRequestError('Training Plan', data.get('_id'))
                update_query = validate_training_plan_entry_data(data, False)
                id_to_update = data.get('_id')
                del update_query['_id']
                update_query = {'$set': update_query}
                result = db.training_plan.update_one({"_id": ObjectId(id_to_update)}, update_query)
                if result.matched_count == 0:
                    raise InvalidIdUpdateRequestError('Training Plan', data.get('_id'))
                return json.loads(str(Response(success=True, data=str(result.upserted_id))))
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
                    target_exercises = db.exercise.find(filter=criteria, limit=limit, projection={"_id": 1})
                    criteria = {"exerciseCompositions.exercises": {'$in': target_exercises}}
                    raw_results = db.training_plan.find(filter=criteria, limit=limit)
                    for result in raw_results:
                        exercises = []
                        exercise_composition = result['exerciseCompositions']
                        for exercise in exercise_composition['exercises']:
                            exercises.append(fetch_data_for_exercise(exercise))
                        result['exerciseCompositions']['exercises'] = exercises
                        results.append(utils.bson_to_json(result))
                LOGGER.info('response sent %s', str(Response(success=True, data=results)))
                return json.loads(str(Response(success=True, data=results)))
            else:
                raise InvalidOperationError(operation)

        except InvalidRequestError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceStructureError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidOperationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidResourceParameterError as e:
            return json.loads(str(ErrorResponse(e)))
        except DuplicateResourceCreationError as e:
            return json.loads(str(ErrorResponse(e)))
        except InvalidIdUpdateRequestError as e:
            return json.loads(str(ErrorResponse(e)))

    @user_auth.login_required
    def delete(self, obj_id):
        result = db.exercise.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)


def fetch_data_for_exercise(raw_result):
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
    return result


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


def validate_exercise_entry_data(data, create=True):
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'Exercise')
    if data.get('majorMuscles') is None or data.get('majorMuscles').__len__ == 0:
        raise InvalidResourceStructureError('majorMuscle', 'Exercise')
    if data.get('repetition') is None and data.get('duration') is None:
        raise InvalidResourceStructureError('Either repetition or duration', 'Exercise')
    if data.get('repetition') is not None and data.get('duration') is not None:
        raise InvalidResourceStructureError('Only one of repetition or duration', 'Exercise')

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
    if create:
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
    return data


def validate_muscle_group_entry_data(data, create=True):
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'MuscleGroup')
    if data.get('muscles') is None or data.get('muscles').__len__() < 1:
        raise InvalidResourceStructureError('muscles', 'MuscleGroup')
    if data.get('imageURLs') is None:
        data.update({'imageURLs': []})
    if create:
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
    return data


def validate_muscle_entry_data(data, create=True):
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'Muscle')
    if data.get('imageURLs') is None:
        data.update({'imageURLs': []})
    if create:
        duplicate_check_query = db.muscle.find_one(filter={"name": data.get('name')})
        if duplicate_check_query is not None:
            raise DuplicateResourceCreationError(data.get('name'), 'Muscle')
    return data


def validate_equipment_entry_data(data, create=True):
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'Equipment')
    if data.get('type') is None or data.get('name') == "":
        raise InvalidResourceStructureError('equipment_type', 'Equipment')
    if data.get('detail') is None:
        data.update({"detail": ""})
    if data.get('imageURLs') is None:
        data.update({"imageURLs": []})
    if create:
        duplicate_check_query = db.equipment.find_one(filter={"name": data.get('name')})
        if duplicate_check_query is not None:
            raise DuplicateResourceCreationError(data.get('name'), 'Equipment')
    type_result = db.equipment_type.find_one({"name": data.get('type')})
    if type_result is not None:
        data['type'] = type_result['_id']
    else:
        data['type'] = db.equipment_type.insert_one({"name": data.get('type')}).inserted_id
    return data


def validate_training_plan_entry_data(data, create=True):
    if data.get('name') is None or data.get('name') == "":
        raise InvalidResourceStructureError('name', 'TrainingPlan')
    if data.get('exerciseCompositions') is None or data.get('exerciseCompositions').__len__() < 1:
        raise InvalidResourceStructureError('exerciseCompositions', 'TrainingPlan')
    # if data.get('owner') is None:
    #     raise InvalidResourceCreationError('exerciseCompositions', 'owner')
    if data.get('participants') is None:
        data.update({'participants': []})
    if create:
        data.update({'createTime':datetime.datetime.utcnow()})
        data.update({'lastModified': data.get('createTime')})
        duplicate_check_query = db.training_plan.find_one(filter={"name": data.get('name')})
        if duplicate_check_query is not None:
            raise DuplicateResourceCreationError(data.get('name'), 'TrainingPlan')

    exercise_compositions = []
    for exerciseComposition in data.get('exerciseCompositions'):
        if exerciseComposition.get('name') is None:
            exerciseComposition.update({'name': ''})
        if exerciseComposition.get('repetition') is None:
            exerciseComposition.update({'repetition': 0})
        for exercise_id in exerciseComposition.get('exercises'):
            exercise_query = db.exercise.find_one({"_id": ObjectId(exercise_id)})
            if exercise_query is None:
                raise InvalidResourceParameterError(exercise_id, 'exercises')
        exercise_compositions.append(exerciseComposition)
    data['exerciseCompositions'] = exercise_compositions
    return data


def validate_user_privilege(operation, resource_type):
    auth_type, token = request.headers['Authorization'].split(
        None, 1)
    claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256', options={'verify_exp': False})
    user_level = claim.get('level')
    privilege_group = PRIVILEGE_GROUP[user_level]
    if operation == 'create':
        if privilege_group['c'] != 'all' and resource_type not in privilege_group['c']:
            raise AttemptedToAccessRestrictedResourceError(resource_type)
    elif operation == 'query':
        if privilege_group['r'] != 'all' and resource_type not in privilege_group['r']:
            raise AttemptedToAccessRestrictedResourceError(resource_type)
    elif operation == 'update':
        if privilege_group['u'] != 'all' and resource_type not in privilege_group['u']:
            raise AttemptedToAccessRestrictedResourceError(resource_type)



