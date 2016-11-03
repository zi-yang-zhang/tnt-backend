import json
import bson.json_util

from exception import InvalidAuthHeaderException


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


def non_empty_str(string):
    if string == "":
        raise ValueError("This string cannot be empty")
    return string


def non_empty_and_no_space_str(string):
    if string == "":
        raise ValueError("This string cannot be empty")
    if " " in string:
        raise ValueError("This string cannot have space")
    return string


def bearer_header_str(bearer_header):
    if bearer_header == "":
        raise InvalidAuthHeaderException("Invalid Authorization header type")
    try:
        auth_type, token = bearer_header.split(None, 1)
    except ValueError:
        raise InvalidAuthHeaderException("Invalid Authorization header type")
    if auth_type != 'Bearer':
        raise InvalidAuthHeaderException("Invalid Authorization header type")
    elif token is None or token == "":
        raise InvalidAuthHeaderException("Invalid Authorization header type")
    return token