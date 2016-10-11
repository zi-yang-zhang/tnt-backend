import json


class Response(object):
    def __init__(self, success, data=None):
        self.data = data
        self.success = success

    def set_data(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.__dict__)


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
