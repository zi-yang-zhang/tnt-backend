import model
import gym
import user
# from authenticator import AdminAuthToken, WechatAuthToken
from flask import Blueprint
from flask_restful import Api

model_api = Blueprint('model_api', __name__)
model_api_router = Api(model_api)

# router.add_resource(model.Equipment, '/api/equipment/<string:obj_id>', '/api/equipment/')
# router.add_resource(model.EquipmentType, '/api/equipment_type/<string:obj_id>', '/api/equipment_type/')
# router.add_resource(model.Muscle, '/api/muscle/<string:obj_id>', '/api/muscle/')
# router.add_resource(model.MuscleGroup, '/api/muscle_group/<string:obj_id>', '/api/muscle_group/')
# router.add_resource(model.ExerciseMetric, '/api/exercise_metric/<string:obj_id>', '/api/exercise_metric/')
# router.add_resource(model.CategoryTag, '/api/category_tag/<string:obj_id>', '/api/category_tag/')
# router.add_resource(model.Exercise, '/api/exercise/<string:obj_id>', '/api/exercise/')
# router.add_resource(AdminAuthToken, '/api/auth/')
# router.add_resource(WechatAuthToken, '/api/wechat_auth')
model_api_router.add_resource(gym.Gym, '/api/gym/')
model_api_router.add_resource(gym.Merchandise, '/api/merchandise/')
model_api_router.add_resource(user.User, '/api/user/')




