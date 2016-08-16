import logging
from logging.config import fileConfig
from flask import send_from_directory, request, make_response, redirect
from jose import jwt, JWTError
import os
from flask import Flask
from router import router_blueprint, router


app = Flask('tnt-core', static_folder='./static')
app.config.from_pyfile(os.environ['setting'])
router.init_app(app)
app.register_blueprint(router_blueprint)
logging.getLogger('flask_cors').level = logging.DEBUG if app.debug else logging.INFO
fileConfig('logging_config.ini')
logger = app.logger


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
    return r