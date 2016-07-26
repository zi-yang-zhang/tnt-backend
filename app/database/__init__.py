from flask_pymongo import PyMongo
from pymongo import ALL

main_driver = PyMongo()
admin_driver = PyMongo()

# main = main_driver.db
# admin = admin_driver.db

# main.set_profiling_level(level=ALL)
# admin.set_profiling_level(level=ALL)
