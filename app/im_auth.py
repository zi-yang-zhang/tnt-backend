from flask import Blueprint, current_app as app
from flask import request
from flask_restful import Api, Resource, reqparse

from basic_response import Response
from database import user_db
from utils import bearer_header_str


class IsUser(Resource):
    def get(self):
        app.logger.debug(str(request.args))
        app.logger.debug(str(request.headers))
        parser = reqparse.RequestParser()
        parser.add_argument('user', trim=True, type=str, location='args')
        args = parser.parse_args()
        user_result = user_db.user.find_one(filter={"username": args['user']})
        if user_result is None:
            return Response(success=False).__dict__, 404
        else:
            return Response(success=True).__dict__, 200


class Auth(Resource):

    def get(self):
        app.logger.debug(str(request.args))
        app.logger.debug(str(request.headers))

        # parser = reqparse.RequestParser()
        # parser.add_argument('Authorization', trim=True, type=bearer_header_str, nullable=False, location='headers',
        #                     required=True, help='Needs to be logged in to view transaction records')
        return Response(success=True).__dict__, 200


im_auth_api = Blueprint("im_auth_api", __name__, url_prefix='/api/internal/chat')
im_api_router = Api(im_auth_api)
im_api_router.add_resource(IsUser, '/is_user')
im_api_router.add_resource(Auth, '/auth')
