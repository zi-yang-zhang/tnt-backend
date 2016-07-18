from core import app
from flask_cors import CORS
from router import router_blueprint, router

router.init_app(app)
app.register_blueprint(router_blueprint)

app.config.from_pyfile('dev-settings.py')

if app.config['DEBUG_SERVER']:
    CORS(app=app, supports_credentials=True, expose_headers='.*')
    if __name__ == '__main__':
        app.run(host="0.0.0.0", debug=True, port=2001, threaded=True)
elif app.debug:
    if __name__ == '__main__':
        app.run(host="0.0.0.0", debug=True, port=2001, threaded=True)
else:
    if __name__ == '__main__':
        app.run(host="0.0.0.0", port=2001)
