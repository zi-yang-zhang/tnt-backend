import os
from flask import request
from flask_restful import Resource
from bson.objectid import ObjectId
from bson.json_util import dumps
import json
import utils
import logging
from pymongo import MongoClient, ALL
from pymongo.collection import ReturnDocument


client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
db = client.dev


def initialize():
    db.set_profiling_level(level=ALL)


class EquipmentType(Resource):

    def post(self):
        args = request.get_json()
        result = db.equipment_type.insert_one(args['data']).inserted_id
        return result.encode('utf-8')

    def get(self, obj_id):
        result = db.equipment_type.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(result)

    def delete(self, obj_id):
        result = db.equipment_type.delete_one({"_id": ObjectId(obj_id)})
        return result.encode('utf-8')


class Equipment(Resource):

    def delete(self, obj_id):
        result = db.equipment.delete_one({"_id": ObjectId(obj_id)})
        return result.encode('utf-8')

    def get(self, obj_id):
        result = db.equipment.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return result
        return utils.bson_to_json(json.loads(dumps(result)))

    def post(self):
        args = request.get_json()
        operation = args['operation']
        logging.getLogger().debug(operation)
        data = args['data']

        if operation == 'create':
            equipment_type = data['type']
            type_result = db.equipment_type.find_one({"name": equipment_type['name']})
            if type_result is not None:
                data['type'] = utils.bson_to_json(type_result)['_id']
            else:
                data['type'] = str(db.equipment_type.insert_one(data['type']).inserted_id)
            new_id = db.equipment.insert_one(data).inserted_id
            return str(new_id)
        elif operation == 'update':
            raise NotImplementedError
        elif operation == 'query':
            name_field = data.get('name')
            type_field = data.get('type')
            limit = data['find']
            if name_field is not None:
                return utils.bson_to_json(db.equipment.find(filter={"name": utils.translate_query(name_field)}, limit=limit)[0])
            return None


class Muscle(Resource):
    def put(self, request, **kwargs):
        return super(Muscle, self).put(request, **kwargs)

    def delete(self, request, **kwargs):
        return super(Muscle, self).delete(request, **kwargs)

    def get(self, request, **kwargs):
        return super(Muscle, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(Muscle, self).post(request, **kwargs)


class MuscleGroup(Resource):
    def put(self, request, **kwargs):
        return super(MuscleGroup, self).put(request, **kwargs)

    def delete(self, request, **kwargs):
        return super(MuscleGroup, self).delete(request, **kwargs)

    def get(self, request, **kwargs):
        return super(MuscleGroup, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(MuscleGroup, self).post(request, **kwargs)


class ExerciseMetric(Resource):

    def put(self, request, **kwargs):
        return super(ExerciseMetric, self).put(request, **kwargs)

    def delete(self, request, **kwargs):
        return super(ExerciseMetric, self).delete(request, **kwargs)

    def get(self, request, **kwargs):
        return super(ExerciseMetric, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(ExerciseMetric, self).post(request, **kwargs)


class CategoryTag(Resource):
    def put(self, request, **kwargs):
        return super(CategoryTag, self).put(request, **kwargs)

    def delete(self, request, **kwargs):
        return super(CategoryTag, self).delete(request, **kwargs)

    def get(self, request, **kwargs):
        return super(CategoryTag, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(CategoryTag, self).post(request, **kwargs)


