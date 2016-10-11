from calendar import timegm
from datetime import datetime

from bson import ObjectId
from flask import Blueprint
from flask import current_app as app
from flask_restful import Api, reqparse, Resource

from basic_response import Response
from database import transaction_db, gym_db, user_db
from exception import TransactionGymNotFound, TransactionPaymentTypeNotSupported, \
    TransactionUserNotFound, TransactionMerchandiseNotFound, TransactionRecordNotFound
from utils import non_empty_str

SUPPORTED_PAYMENT_TYPE = {'wechat'}
TRANSACTION_STATE = {"pending": 1, "success": 2, "failed": 3, "canceled": 4}


def verify_wechat_transaction(transaction_id):
    app.logger.info('Start verifying wechat transaction: ' + transaction_id)
    return True


class Verify(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('transactionId', required=True, trim=True, type=non_empty_str, nullable=False, help='transactionId is required')
        parser.add_argument('transactionRecordId', required=True, trim=True, type=non_empty_str, nullable=False, help='transactionRecordId is required')
        args = parser.parse_args()
        transaction_record_id = args['transactionRecordId']
        transaction_record = transaction_db.transaction.find_one({"_id": ObjectId(transaction_record_id)})
        if transaction_record is None:
            raise TransactionRecordNotFound(transaction_record_id)
        transaction_verified = verify_wechat_transaction(args['transactionId'])
        update_query = {'transactionId': args['transactionId']}
        data = None
        if not transaction_verified:
            update_query['transactionState'] = TRANSACTION_STATE["failed"]
        else:
            update_query['transactionState'] = TRANSACTION_STATE["success"]
        transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, {'$set': update_query})
        transaction_record = transaction_db.transaction.find_one({"_id": ObjectId(transaction_record_id)})
        if transaction_verified:
            data = transaction_record
            data.update({'_id': str(data.get("_id"))})
        response = Response(success=transaction_verified, data=data).__dict__
        return response, 200


class Cancel(Resource):

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('transactionRecordId', required=True, type=non_empty_str, nullable=False)
        args = parser.parse_args()
        transaction_record_id = args['transactionRecordId']
        update_query = {'$set': {"transactionState": TRANSACTION_STATE["canceled"]}}
        transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_query)
        response = Response(success=True).__dict__
        return response, 200


class Initiate(Resource):

    def post(self):
        app.logger.debug('Initiate transaction')
        parser = reqparse.RequestParser()
        parser.add_argument('userEmail', required=True, trim=True, type=non_empty_str, nullable=False, help='User email is required')
        parser.add_argument('gymId', required=True, type=non_empty_str, nullable=False, help='gymId is required')
        parser.add_argument('merchandiseId', required=True, type=non_empty_str, nullable=False, help='merchandiseId is required')
        parser.add_argument('paymentType', required=True, type=non_empty_str, nullable=False, help='paymentType is required')
        args = parser.parse_args()
        user_email = args['userEmail']
        gym_id = args['gymId']
        merchandise_id = args['merchandiseId']
        payment_type = args['paymentType']
        transaction = Transaction(user_email=user_email, gym_id=gym_id, merchandise_id=merchandise_id,
                                  payment_type=payment_type)
        return transaction.initiate_transaction()


class Transaction:
    user_email = None
    gym_id = None
    merchandise_id = None
    payment_type = None

    def __init__(self, user_email, gym_id, merchandise_id, payment_type):
        self.user_email = user_email
        self.gym_id = gym_id
        self.merchandise_id = merchandise_id
        self.payment_type = payment_type
        gym_result = gym_db.gym.find_one({"_id": ObjectId(gym_id)})
        user_result = user_db.user.find_one({"email": user_email})
        merchandise_result = gym_db.merchandise.find_one({"_id": ObjectId(merchandise_id)})
        if gym_result is None:
            raise TransactionGymNotFound(gym_id)
        if user_result is None:
            raise TransactionUserNotFound(user_email)
        if merchandise_result is None:
            raise TransactionMerchandiseNotFound(merchandise_id)
        if payment_type not in SUPPORTED_PAYMENT_TYPE:
            raise TransactionPaymentTypeNotSupported(payment_type)
        pass

    def initiate_transaction(self):
        merchandise = gym_db.merchandise.find_one({"_id": ObjectId(self.merchandise_id)})
        prepay_id = self.request_wechat_payment()
        transaction = {"recipient": self.gym_id,
                       "payer": self.user_email,
                       "paymentMethod": self.payment_type,
                       "merchandiseId": self.merchandise_id,
                       "transactionState": TRANSACTION_STATE["pending"],
                       "createdDate": timegm(datetime.utcnow().utctimetuple()),
                       "startDate": merchandise.get('expiryInfo').get('startDate'),
                       "expiryDate": merchandise.get('expiryInfo').get('expiryDate')
                       }
        transaction_record_id = transaction_db.transaction.insert_one(transaction).inserted_id

        response = Response(success=True,
                                    data={
                                        "prepayId": prepay_id,
                                        "transactionRecordId": str(transaction_record_id)}).__dict__
        return response, 201


    def request_wechat_payment(self):
        app.logger.info('Start Requesting wechat payment prepay_id')
        return "prepay_id"


transaction_api = Blueprint("transaction_api", __name__, url_prefix='/api/transaction')
transaction_api_router = Api(transaction_api)
transaction_api_router.add_resource(Initiate, '/initiate')
transaction_api_router.add_resource(Verify, '/verify')
transaction_api_router.add_resource(Cancel, '/cancel')

