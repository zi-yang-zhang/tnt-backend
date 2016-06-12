from flask_restful import Api
from flask import Blueprint
import model
router = Api()
router_blueprint = Blueprint('router', __name__)


router.add_resource(model.EquipmentType, '/equipment/<string:obj_id>', '/equipment/')
