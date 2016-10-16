import os
from pymongo import MongoClient, ALL, GEOSPHERE
from flask import current_app


client = MongoClient(os.environ['MONGO_PORT_27017_TCP_ADDR'], 27017, connect=False)
resource_db = client.main
admin_db = client.admin
user_db = client.user
gym_db = client.gym
transaction_db = client.transaction
USER_LEVEL = {'DBA': 0, 'SystemAdmin': 1, 'Admin': 2, 'PowerUser': 3, 'User': 4, 'Guest': 5}


def initialize():
    current_app.logger.info('Initialize Database')
    resource_db.set_profiling_level(level=ALL)
    admin_db.set_profiling_level(level=ALL)
    gym_db.set_profiling_level(level=ALL)
    gym_db.gym.create_index([("geoLocation", GEOSPHERE)], background=True)


