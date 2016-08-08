import logging
import sys

from flask_cors import CORS

from core import app as application

try:
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
