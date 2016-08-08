import os

DEBUG = True
SECRET_KEY = 'secret_key'
DEBUG_SERVER = True
CELERY_BROKER_URL = os.environ['BROKER_URL']
CELERY_BACKEND = 'rpc://'
