

class TransactionMerchandiseNotFound(Exception):
    def __init__(self, merchandise_id):
        self.code = "TX1000"
        self.message = "Error Merchandise not found: " + merchandise_id


class TransactionUserNotFound(Exception):
    def __init__(self, user_email):
        self.code = "TX1001"
        self.message = "Error User not found: " + user_email


class TransactionGymNotFound(Exception):
    def __init__(self, gym_id):
        self.code = "TX1002"
        self.message = "Error Gym not found: " + gym_id


class TransactionPaymentMethodNotSupported(Exception):
    def __init__(self, payment_type):
        self.code = "TX1003"
        self.message = "Error Transaction Method not supported: " + payment_type


class TransactionRecordNotFound(Exception):
    def __init__(self, transaction_record_id):
        self.code = "TX1004"
        self.message = "Error Transaction record not found: " + transaction_record_id


class TransactionRecordInvalidState(Exception):
    def __init__(self, transaction_record_id, state):
        self.code = "TX1005"
        self.message = "Error Transaction record {} with invalid state:{} ".format(transaction_record_id, state)


class TransactionRecordExpired(Exception):
    def __init__(self, transaction_record_id):
        self.code = "TX1006"
        self.message = "Error Transaction record {} expired".format(transaction_record_id)


class TransactionRecordCountUsedUp(Exception):
    def __init__(self, transaction_record_id):
        self.code = "TX1007"
        self.message = "Error Transaction record {} count is used up".format(transaction_record_id)


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
        self.message = "Resource exists with <" + name + "> for " + resource_type


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


class InvalidAuthHeaderException(Exception):
    def __init__(self, message):
        self.code = "A1000"
        self.message = message