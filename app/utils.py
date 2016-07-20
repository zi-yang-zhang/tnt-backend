import json
import bson.json_util


def prettify_bson(bson_string):
    bson_string['_id'] = bson_string['_id']['$oid']
    return bson_string


def translate_query(query):
    equals_query = query.get('equals')
    contains_query = query.get('contains')
    if equals_query is not None:
        return equals_query
    if contains_query is not None:
        return {"$regex": ".*{}.*".format(contains_query.encode('utf-8'))}
    raise InvalidQueryOperatorError(query)


def bson_to_json(bson_string):
    return prettify_bson(json.loads(bson.json_util.dumps(bson_string)))


class InvalidQueryOperatorError(Exception):
    def __init__(self, query):
        self.message = "Invalid query operation: " + str(query)
