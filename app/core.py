import json
import logging
from logging.config import fileConfig

from bson.errors import InvalidId
from flask import send_from_directory, request, make_response, redirect, jsonify
from jose import jwt, JWTError
import os
from flask import Flask
from pymongo.errors import WriteError
import ast

from basic_response import DuplicateResourceCreationError, InvalidRequestError, MongoErrorResponse, \
    InvalidResourceStructureError, InvalidResourceParameterError, InvalidIdUpdateRequestError, \
    AttemptedToAccessRestrictedResourceError, InvalidRequestParamErrorResponse

from basic_response import ErrorResponse
from router import router_blueprint, router
import database

app = Flask('tnt-core', static_folder='./static')
app.config.from_pyfile(os.environ['setting'])
router.init_app(app)
app.register_blueprint(router_blueprint)
logging.getLogger('flask_cors').level = logging.DEBUG if app.debug else logging.INFO
fileConfig('logging_config.ini')
logger = app.logger
with app.app_context():
    database.initialize()


@app.route('/')
def index():
    access_token = request.cookies.get('jwt')
    logger.info("access_token %s", access_token)
    if access_token is not None:
        try:
            jwt.decode(token=access_token, key=app.secret_key, algorithms='HS256')
            return make_response(redirect('/dashboard'))
        except JWTError as e:
            logger.info("jwt not verified: %s", type(e).__name__)
            return send_from_directory('template', 'login.html')
    else:
        return send_from_directory('template', 'login.html')


@app.route('/dashboard/', defaults={'path': ''})
@app.route('/dashboard', defaults={'path': ''})
@app.route('/dashboard/<path:path>')
def dashboard(path):
    access_token = request.cookies.get('jwt')
    logger.debug("access_token %s", access_token)
    if access_token is not None:
        try:
            jwt.decode(token=access_token, key=app.secret_key, algorithms='HS256')
            return send_from_directory('template', 'app.html')
        except JWTError as e:
            logger.info("jwt not verified: %s", type(e).__name__)
            return make_response(redirect('/'))
    else:
        return make_response(redirect('/'))


@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    payload = json.loads(r.get_data())
    if payload.get('message') is not None:
        r.set_data(InvalidRequestParamErrorResponse(payload.get('message')))
    return r


# Resource errors
@app.errorhandler(DuplicateResourceCreationError)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 400
    return response


@app.errorhandler(InvalidRequestError)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 400
    return response


@app.errorhandler(WriteError)
def handle_invalid_usage(error):
    response = jsonify(MongoErrorResponse(error).__dict__)
    response.status_code = 400
    return response


@app.errorhandler(InvalidResourceStructureError)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 400
    return response


@app.errorhandler(InvalidResourceParameterError)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 400
    return response


@app.errorhandler(InvalidIdUpdateRequestError)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 400
    return response


@app.errorhandler(AttemptedToAccessRestrictedResourceError)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 401
    return response


@app.errorhandler(TypeError)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 400
    return response


@app.errorhandler(InvalidId)
def handle_invalid_usage(error):
    response = jsonify(ErrorResponse(error).__dict__)
    response.status_code = 400
    return response

