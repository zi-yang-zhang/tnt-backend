import os
from flask import Flask
from router import router_blueprint, router


def create_app():
    app = Flask(__name__, static_folder='./static')
    app.config.from_pyfile(os.environ['setting'])
    router.init_app(app)
    app.register_blueprint(router_blueprint)
    return app
