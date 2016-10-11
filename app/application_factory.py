import json
import logging
import os
from logging.config import fileConfig

from bson.errors import InvalidId
from flask import Flask
from flask import jsonify
from pymongo.errors import WriteError

import exception
from basic_response import InvalidRequestParamErrorResponse, MongoErrorResponse, ErrorResponse
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

    @application.errorhandler(exception.TransactionGymNotFound)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 404
        return response

    @application.errorhandler(exception.TransactionPaymentTypeNotSupported)
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
        response.status_code = 400
        return response

    @application.errorhandler(DuplicatedUsername)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 400
        return response

    @application.errorhandler(404)
    def handle_invalid_usage(error):
        response = jsonify(ErrorResponse(error).__dict__)
        response.status_code = 404
        return response

    application.config.from_pyfile(os.environ['setting'])
    from router import router_blueprint
    application.register_blueprint(router_blueprint)
    from transaction import transaction_api
    application.register_blueprint(transaction_api)
    logging.getLogger('flask_cors').level = logging.DEBUG if application.debug else logging.INFO
    fileConfig('logging_config.ini')
    application.after_request(add_header)

    with application.app_context():
        import database
        database.initialize()
    return application


def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    try:
        payload = json.loads(r.get_data())
        if payload.get('message') is not None:
            r.set_data(InvalidRequestParamErrorResponse(payload.get('message')))
    except Exception:
        pass
    return r