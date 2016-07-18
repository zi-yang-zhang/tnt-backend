from flask_restful import Api
from flask import Blueprint
import model
from flask_cors import CORS
from authenticator import AuthToken, TestResource
router = Api()
router_blueprint = Blueprint('router', __name__)
# CORS(router_blueprint)

router.add_resource(model.Equipment, '/equipment/<string:obj_id>', '/equipment/')
router.add_resource(model.EquipmentType, '/equipment_type/<string:obj_id>', '/equipment_type/')
router.add_resource(model.Muscle, '/muscle/<string:obj_id>', '/muscle/')
router.add_resource(model.MuscleGroup, '/muscle_group/<string:obj_id>', '/muscle_group/')
router.add_resource(model.ExerciseMetric, '/exercise_metric/<string:obj_id>', '/exercise_metric/')
router.add_resource(model.CategoryTag, '/category_tag/<string:obj_id>', '/category_tag/')
router.add_resource(model.Exercise, '/exercise/<string:obj_id>', '/exercise/')
router.add_resource(AuthToken, '/api/auth/')
router.add_resource(TestResource, '/api/test/')



