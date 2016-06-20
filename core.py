from flask import Flask
from router import router_blueprint, router
import logging
from logging.config import fileConfig

fileConfig('logging_config.ini')
logger = logging.getLogger()
app = Flask(__name__)
router.init_app(app)
app.register_blueprint(router_blueprint)
