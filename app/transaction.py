from authenticator import user_auth
from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import request, current_app, make_response
from flask_restful import Resource
import utils
from database import transaction_db as db

from basic_response import InvalidResourceStructureError, InvalidResourceParameterError, InvalidOperationError, \
    InvalidRequestError, DuplicateResourceCreationError, InvalidIdUpdateRequestError, AttemptedToDeleteInUsedResource, \
    AttemptedToAccessRestrictedResourceError, Response, ErrorResponse


class TransactionRecord(Resource):

    def get(self, obj_id):
        result = db.transaction_record.find_one({"_id": ObjectId(obj_id)})
        if result is None:
            return Response(False, utils.bson_to_json(result)), 404
        return Response(True, utils.bson_to_json(result))

    def put(self):
        pass