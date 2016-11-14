import json
import logging
import os
from logging.config import fileConfig

from bson.errors import InvalidId
from flask import Flask, jsonify, request
from flask_session import Session
from jose import JWTError
from pymongo.errors import WriteError
from werkzeug.datastructures import Authorization

import exception
from basic_response import InvalidRequestParamErrorResponse, MongoErrorResponse, ErrorResponse, Response
from user import DuplicatedUserEmail, DuplicatedUsername


def create_app():
    application = Flask('tnt-core', static_folder='./static')

    # Resource errors

    @application.errorhandler(exception.DuplicateResourceCreationError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.InvalidRequestError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(WriteError)
    def handle_invalid_usage(error):
        response = jsonify(MongoErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.InvalidResourceStructureError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.InvalidResourceParameterError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.InvalidIdUpdateRequestError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.AttemptedToAccessRestrictedResourceError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 401
        return response

    @application.errorhandler(TypeError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(InvalidId)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.TransactionMerchandiseNotFound)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 404
        return response

    @application.errorhandler(exception.TransactionUserNotFound)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 404
        return response

    @application.errorhandler(exception.TransactionRecordInvalidState)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.TransactionRecordExpired)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 200
        return response

    @application.errorhandler(exception.TransactionRecordCountUsedUp)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 200
        return response

    @application.errorhandler(exception.TransactionGymNotFound)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 404
        return response

    @application.errorhandler(JWTError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 401
        return response

    @application.errorhandler(exception.TransactionPaymentMethodNotSupported)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(exception.TransactionRecordNotFound)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 404
        return response

    @application.errorhandler(DuplicatedUserEmail)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 200
        return response

    @application.errorhandler(DuplicatedUsername)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 200
        return response

    @application.errorhandler(404)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 404
        return response

    @application.errorhandler(exception.AuthenticationUserNotFound)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 401
        return response

    @application.errorhandler(exception.AuthenticationUserPasswordWrong)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 401
        return response

    @application.errorhandler(exception.AuthenticationUserAuthTypeError)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 401
        return response


    @application.before_request
    def print_request():
        pass


    @application.after_request
    def add_header(r):
        """
        Add headers to both force latest IE rendering engine or Chrome Frame,
        and also to cache the rendered page for 10 minutes.
        """
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        r.headers['Content-Type'] = 'application/json'
        try:
            payload = json.loads(r.get_data())
            if payload.get('message') is not None:
                if 'Authorization' in payload.get('message'):
                    r.status_code = 401
                    r.set_data(Response(success=False, exceptionMessage=payload.get('message').get('Authorization')))
                else:
                    r.set_data(InvalidRequestParamErrorResponse(payload.get('message')))
        except Exception:
            pass
        return r

    application.config.from_pyfile(os.environ['setting'])
    Session(app=application)
    from user import user_api
    application.register_blueprint(user_api)
    from gym import gym_api
    application.register_blueprint(gym_api)
    from transaction import transaction_api
    application.register_blueprint(transaction_api)
    from authenticator import auth_api
    application.register_blueprint(auth_api)
    from im_auth import im_auth_api
    application.register_blueprint(im_auth_api)
    logging.getLogger('flask_cors').level = logging.DEBUG if application.debug else logging.INFO
    fileConfig('logging_config.ini')

    with application.app_context():
        import database
        database.initialize()
    return application



