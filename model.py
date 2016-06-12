import os
from flask import request
from flask_restful import Resource
from bson.objectid import ObjectId
from bson.json_util import dumps
from pymongo import MongoClient
from pymongo.collection import ReturnDocument


client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
db = client.dev


class EquipmentType(Resource):

    def post(self):
        args = request.get_json()
        result = db.equipment_type.insert_one(args['data']).inserted_id
        return str(result)

    def get(self, obj_id):
        result = db.equipment_type.find_one({"_id": ObjectId(obj_id)})
        return dumps(result)

    def delete(self, obj_id):
        result = db.equipment_type.delete_one({"_id": ObjectId(obj_id)})
        return str(result)


class Equipment(Resource):

    def delete(self, obj_id):
        result = db.equipment_type.delete_one({"_id": ObjectId(obj_id)})
        return str(result)

    def get(self, obj_id):
        result = db.equipment_type.find_one({"_id": ObjectId(obj_id)})
        return dumps(result)

    def post(self):
        args = request.get_json()
        operation = args['operation']
        data = args['data']

        if operation is 'create':
            equipment_type = data['type']
            type_result = db.equipment_type.find_one({"name": equipment_type['name']})
            if type_result is not None:
                data['type'] = type_result
            else:
                data['type'] = str(db.equipment_type.insert_one(args['data']).inserted_id)
            return db.equipment.insert_one(data).inserted_id
        elif operation is 'update':
            return db.equipment_type.find_one_and_update(data, return_document=ReturnDocument.AFTER)
        elif operation is 'query':
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


