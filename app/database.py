import os
from pymongo import MongoClient, ALL


client = MongoClient(os.environ['MONGO_PORT_27017_TCP_ADDR'], 27017, connect=False)
resource = client.main
admin = client.admin
user = client.user
gym = client.gym
transaction = client.transaction


def initialize():
    resource.set_profiling_level(level=ALL)
    admin.set_profiling_level(level=ALL)
