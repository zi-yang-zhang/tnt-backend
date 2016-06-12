from flask import Flask
from router import router_blueprint, router

app = Flask(__name__)
router.init_app(app)
app.register_blueprint(router_blueprint)
