

class TransactionMerchandiseNotFound(Exception):
    def __init__(self, merchandise_id):
        self.code = "TX1000"
        self.message = "Error Merchandise not found: " + merchandise_id


class TransactionUserNotFound(Exception):
    def __init__(self, user_id):
        self.code = "TX1001"
        self.message = "Error User not found: " + user_id


class TransactionGymNotFound(Exception):
    def __init__(self, gym_id):
        self.code = "TX1002"
        self.message = "Error Gym not found: " + gym_id


class TransactionPaymentTypeNotSupported(Exception):
    def __init__(self, payment_type):
        self.code = "TX1003"
        self.message = "Error Merchandise not found: " + payment_type
