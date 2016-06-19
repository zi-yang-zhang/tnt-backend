from flask_restful import Api
from flask import Blueprint
import model
router = Api()
model.initialize()
router_blueprint = Blueprint('router', __name__)


router.add_resource(model.Equipment, '/equipment/<string:obj_id>', '/equipment/')
router.add_resource(model.EquipmentType, '/equipment_type/<string:obj_id>', '/equipment_type/')

