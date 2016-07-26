from core import app as application
from flask_cors import CORS
from router import router_blueprint, router
import sys
import logging
import os
from database import main_driver, admin_driver

application.config['MONGO_ADMIN_HOST'] = os.environ['MONGO_PORT_27017_TCP_ADDR']
application.config['MONGO_ADMIN_PORT'] = 27017
application.config['MONGO_ADMIN_CONNECT'] = False
application.config['MONGO_ADMIN_DBNAME'] = 'admin'


application.config['MONGO_MAIN_HOST'] = os.environ['MONGO_PORT_27017_TCP_ADDR']
application.config['MONGO_MAIN_PORT'] = 27017
application.config['MONGO_MAIN_CONNECT'] = False
application.config['MONGO_MAIN_DBNAME'] = 'main'

main_driver.init_app(app=application, config_prefix='MONGO_MAIN')
admin_driver.init_app(app=application, config_prefix='MONGO_ADMIN')

router.init_app(application)
application.register_blueprint(router_blueprint)
application.config.from_pyfile(os.environ['setting'])
try:
    logging.getLogger().debug(application.config.get('DEBUG_SERVER'))
    if application.config.get('DEBUG_SERVER'):
        CORS(app=application, supports_credentials=True, expose_headers='.*')
        if __name__ == '__main__':
            application.run(host="0.0.0.0", debug=True, port=2001, threaded=True)
    elif application.debug:
        if __name__ == '__main__':
            application.run(host="0.0.0.0", debug=True, port=2001, threaded=True)
except:
    e = sys.exc_info()[0]
    logging.getLogger().error(e)
