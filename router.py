from flask_restful import Api
from flask import Blueprint
import model
from authenticator import AuthToken
router = Api()
router_blueprint = Blueprint('router', __name__)

router.add_resource(model.Equipment, '/api/equipment/<string:obj_id>', '/api/equipment/')
router.add_resource(model.EquipmentType, '/api/equipment_type/<string:obj_id>', '/api/equipment_type/')
router.add_resource(model.Muscle, '/api/muscle/<string:obj_id>', '/api/muscle/')
router.add_resource(model.MuscleGroup, '/api/muscle_group/<string:obj_id>', '/api/muscle_group/')
router.add_resource(model.ExerciseMetric, '/api/exercise_metric/<string:obj_id>', '/api/exercise_metric/')
router.add_resource(model.CategoryTag, '/api/category_tag/<string:obj_id>', '/api/category_tag/')
router.add_resource(model.Exercise, '/api/exercise/<string:obj_id>', '/api/exercise/')
router.add_resource(AuthToken, '/api/auth/')



