import json
from flask import jsonify


class Response(object):
    def __init__(self, success, data=None, exceptionMessage=None):
        self.data = data
        self.success = success
        self.exceptionMessage = exceptionMessage

    def set_data(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.__dict__)

    def get_resp(self):
        return jsonify(
            data=self.data,
            success=self.success,
            exceptionMessage=self.exceptionMessage)


class MongoErrorResponse(Response):
    def __init__(self, exception):
        super(MongoErrorResponse, self).__init__(success=False)
        self.errorCode = exception.code
        self.exceptionMessage = str(exception.details)


class InvalidRequestParamErrorResponse(Response):
    def __init__(self, message):
        super(InvalidRequestParamErrorResponse, self).__init__(success=False)
        self.exceptionMessage = message


class ErrorResponse(Response):
    def __init__(self, exception):
        super(ErrorResponse, self).__init__(success=False)
        if hasattr(exception, 'code'):
            self.errorCode = exception.code
        self.exceptionMessage = str(exception.message)
