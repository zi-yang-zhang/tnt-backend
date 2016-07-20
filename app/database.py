import os
from pymongo import MongoClient, ALL


client = MongoClient(os.environ['DB_PORT_27017_TCP_ADDR'], 27017)
resource = client.dev
admin = client.admin


def initialize():
    resource.set_profiling_level(level=ALL)
    admin.set_profiling_level(level=ALL)
