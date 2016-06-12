import os
from flask import request
from flask_restful import Resource, reqparse
from bson.objectid import ObjectId
from pymongo import MongoClient


client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
db = client.dev


class EquipmentType(Resource):

    def put(self, request, **kwargs):
        return super(EquipmentType, self).put(request, **kwargs)

    def post(self):
        args = request.get_json()
        created_id = db.equipement_type.insert(args['data']).inserted_id
        return created_id

    def get(self, obj_id):
        result = db.equipement_type.find_one({"_id": ObjectId(obj_id)})
        return str(result)

    def delete(self, request, **kwargs):
        return super(EquipmentType, self).delete(request, **kwargs)


class Equipment(Resource):
    def put(self, request, **kwargs):
        return super(Equipment, self).put(request, **kwargs)

    def delete(self, request, **kwargs):
        return super(Equipment, self).delete(request, **kwargs)

    def get(self, request, **kwargs):
        return super(Equipment, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(Equipment, self).post(request, **kwargs)


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


