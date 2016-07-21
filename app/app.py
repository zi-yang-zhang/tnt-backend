from core import app as application
from flask_cors import CORS
from router import router_blueprint, router
import sys


router.init_app(application)
application.register_blueprint(router_blueprint)

application.config.from_pyfile('settings.py')
try:
    if application.config.get('DEBUG_SERVER'):
        CORS(app=application, supports_credentials=True, expose_headers='.*')
        if __name__ == '__main__':
            application.run(host="0.0.0.0", debug=True, port=2001, threaded=True)
    elif application.debug:
        if __name__ == '__main__':
            application.run(host="0.0.0.0", debug=True, port=2001, threaded=True)
    else:
        if __name__ == '__main__':
            application.run(host="0.0.0.0")
except:
    e = sys.exc_info()[0]
    application.logger.error(e)
