from flask import Flask, send_from_directory
import logging
from logging.config import fileConfig

app = Flask(__name__, static_folder='./static')
logging.getLogger('flask_cors').level = logging.DEBUG if app.debug else logging.INFO
fileConfig('logging_config.ini')
logger = logging.getLogger()


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    return send_from_directory('template', 'app.html')


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