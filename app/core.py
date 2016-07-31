from flask import Flask, send_from_directory, request, make_response, redirect
import logging
from logging.config import fileConfig
from jose import jwt, JWTError

app = Flask(__name__, static_folder='./static')
logging.getLogger('flask_cors').level = logging.DEBUG if app.debug else logging.INFO
fileConfig('logging_config.ini')
logger = logging.getLogger()


@app.route('/')
def index():
    access_token = request.cookies.get('jwt')
    logger.debug("access_token %s", access_token)
    if access_token is not None:
        try:
            jwt.decode(token=access_token, key=app.secret_key, algorithms='HS256')
            return make_response(redirect('/dashboard'))
        except JWTError as e:
            logger.debug("%s, jwt not verified", str(e))
            return send_from_directory('template', 'login.html')
    else:
        return send_from_directory('template', 'login.html')


@app.route('/dashboard', defaults={'path': ''})
@app.route('/dashboard/<path:path>')
def dashboard(path):
    access_token = request.cookies.get('jwt')
    logger.debug("access_token %s", access_token)
    if access_token is not None:
        try:
            logger.debug(jwt.decode(token=access_token, key=app.secret_key, algorithms='HS256'))
            return send_from_directory('template', 'app.html')
        except JWTError as e:
            logger.debug("%s, jwt not verified", str(e))
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