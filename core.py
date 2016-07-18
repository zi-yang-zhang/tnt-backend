from flask import Flask, send_from_directory
import logging
from logging.config import fileConfig

logging.getLogger('flask_cors').level = logging.DEBUG
fileConfig('logging_config.ini')
logger = logging.getLogger()
app = Flask(__name__, static_folder='./static')
app.config['SECRET_KEY'] = 'dev key'


@app.route('/')
def index():
    return send_from_directory('template', 'login.html')


