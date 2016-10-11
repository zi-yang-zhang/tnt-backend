from flask_cors import CORS

from application_factory import create_app

application = create_app()

if application.config.get('DEBUG_SERVER'):
    CORS(app=application, supports_credentials=True, expose_headers='.*')
    if __name__ == '__main__':
        application.run(host="0.0.0.0", debug=True, port=2001)
elif application.debug:
    if __name__ == '__main__':
        application.run(host="0.0.0.0", debug=True, port=2001)
