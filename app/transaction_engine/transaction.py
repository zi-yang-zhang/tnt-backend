from bson import ObjectId

from app.database import transaction_db, gym_db, user_db
from app.transaction_engine.exception import TransactionGymNotFound, TransactionPaymentTypeNotSupported, TransactionUserNotFound, TransactionMerchandiseNotFound

SUPPORTED_PAYMENT_TYPE = set('wechat')


class Engine:
    user_id = None
    gym_id = None
    merchandise_id = None
    payment_type = None

    def __init__(self, user_id, gym_id, merchandise_id, payment_type):
        self.user_id = user_id
        self.gym_id = gym_id
        self.merchandise_id = merchandise_id
        self.payment_type = payment_type
        gym_result = gym_db.merchandise.find_one({"_id": ObjectId(gym_id)})
        user_result = user_db.merchandise.find_one({"_id": ObjectId(user_id)})
        merchandise_result = gym_db.merchandise.find_one({"_id": ObjectId(merchandise_id)})
        if gym_result is None:
            raise TransactionGymNotFound(gym_id)
        if user_result is None:
            raise TransactionUserNotFound(user_id)
        if merchandise_result is None:
            raise TransactionMerchandiseNotFound(merchandise_id)
        if payment_type not in SUPPORTED_PAYMENT_TYPE:
            raise TransactionPaymentTypeNotSupported(payment_type)
        pass

    def perform_transaction(self):
        pass

    def verify(self):
        pass

    def cancel(self):
        pass
