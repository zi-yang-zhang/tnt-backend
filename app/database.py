import os
from pymongo import MongoClient, ALL
from core import app

mongo_host = os.environ['DB_PORT_27017_TCP_ADDR'] if app.debug else ""
client = MongoClient(mongo_host, 27017)
resource = client.dev
admin = client.admin


def initialize():
    resource.set_profiling_level(level=ALL)
    admin.set_profiling_level(level=ALL)
