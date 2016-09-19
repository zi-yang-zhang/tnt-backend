import json


class InvalidResourceStructureError(Exception):
    def __init__(self, param, resource_type):
        self.code = "E1000"
        self.message = param + " is not valid for " + resource_type


class InvalidResourceParameterError(Exception):
    def __init__(self, param, resource_type):
        self.code = "E1001"
        self.message = param + " cannot be found in " + resource_type


class InvalidOperationError(Exception):
    def __init__(self, param):
        self.code = "E1002"
        self.message = "Operation " + param + " is not supported"


class InvalidRequestError(Exception):
    def __init__(self, param):
        self.code = "E1003"
        self.message = param + " is required for the request"


class DuplicateResourceCreationError(Exception):
    def __init__(self, name, resource_type):
        self.code = "E1004"
        self.message = "Resource exists with name <" + name + "> for " + resource_type


class InvalidIdUpdateRequestError(Exception):
    def __init__(self, name, _id):
        self.code = "E1005"
        self.message = name + " with " + _id + " not found" if _id is not None else "id missing in request"


class AttemptedToDeleteInUsedResource(Exception):
    def __init__(self, name, resources):
        self.code = "E1006"
        self.message = "Attempted to delete " + name + ", used by " + str(resources)


class AttemptedToAccessRestrictedResourceError(Exception):
    def __init__(self, resources):
        self.code = "E1007"
        self.message = "Attempted to access restricted resource:" + str(resources)


class NotSupportedOperationError(Exception):
    def __init__(self, operation, resources):
        self.code = "E1008"
        self.message = operation + " is not supported for " + str(resources)


class Response(object):
    def __init__(self, success, data=None):
        if data is None:
            self.data = {}
        else:
            self.data = data
        self.success = success

    def set_data(self, data):
        self.data = data

    def __str__(self):
        return json.dumps(self.__dict__)


class ErrorResponse(Response):
    def __init__(self, exception):
        super(ErrorResponse, self).__init__(success=False)
        if hasattr(exception, 'code'):
            self.errorCode = exception.code
        self.exceptionMessage = str(exception.message)
