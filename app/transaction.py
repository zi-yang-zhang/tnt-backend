import dateutil.parser
from datetime import datetime
from calendar import timegm
from bson import ObjectId
from flask import Blueprint
from flask import current_app
from flask import current_app as app
from flask_restful import Api, reqparse, Resource
from jose import jwt

from basic_response import Response
from database import transaction_db, gym_db, user_db
from exception import TransactionGymNotFound, TransactionPaymentMethodNotSupported, \
    TransactionUserNotFound, TransactionMerchandiseNotFound, TransactionRecordNotFound, TransactionRecordInvalidState, \
    TransactionRecordExpired, TransactionRecordCountUsedUp, InvalidAuthHeaderException
from utils import non_empty_str
from gym import EXPIRY_INFO_TYPE

SUPPORTED_PAYMENT_METHOD = {'wechat'}
TRANSACTION_STATE = {"pending": 1, "success": 2, "failed": 3, "canceled": 4, "expired": 5}


def verify_wechat_transaction(transaction_id):
    app.logger.info('Start verifying wechat transaction: ' + transaction_id)
    return True


class Consume(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('transactionRecordId', required=True, trim=True, type=non_empty_str, nullable=False,
                            help='transactionRecordId is required')
        args = parser.parse_args()
        transaction_record_id = args['transactionRecordId']
        transaction_record = transaction_db.transaction.find_one({"_id": ObjectId(transaction_record_id)})
        if transaction_record is None:
            raise TransactionRecordNotFound(transaction_record_id)
        if transaction_record.get('transactionState') != TRANSACTION_STATE["success"]:
            raise TransactionRecordInvalidState(transaction_record_id, transaction_record.get('transactionState'))
        if transaction_record.get('expiryInfo').get('type') == EXPIRY_INFO_TYPE["by_count"]:
            exp_date = transaction_record.get('expiryInfo').get('expiryDate')
            if dateutil.parser.parse(exp_date) < datetime.utcnow():
                update_command = {'$set': {'transactionState': TRANSACTION_STATE["expired"]}}
                transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_command)
                raise TransactionRecordExpired(transaction_record_id)
            elif transaction_record.get('expiryInfo').get('count') <= 0:
                update_command = {'$set': {'transactionState': TRANSACTION_STATE["expired"]}}
                transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_command)
                raise TransactionRecordCountUsedUp(transaction_record_id)
            else:
                updated_count = transaction_record.get('expiryInfo').get('count') - 1
                update_query = {'expiryInfo.count': updated_count}
                if updated_count == 0:
                    update_query['transactionState'] = TRANSACTION_STATE["expired"]
                update_command = {'$set': update_query, '$push': {'visitRecords': {'date': str(datetime.datetime.utcnow())}}}
                transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_command)
                return Response(success=True).__dict__, 200
        elif transaction_record.get('expiryInfo').get('type') == EXPIRY_INFO_TYPE["by_duration"]:
            start_date = transaction_record.get('createdDate')
            expiry_date = timegm(dateutil.parser.parse(start_date).utctimetuple()) + transaction_record.get(
                'expiryInfo').get('duration')
            if datetime.utcfromtimestamp(expiry_date) < datetime.utcnow():
                update_query = {'transactionState': TRANSACTION_STATE["expired"]}
                update_command = {'$set': update_query}
                transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_command)
                raise TransactionRecordExpired(transaction_record_id)
            else:
                update_command = {'$push': {'visitRecords': {'date': str(datetime.datetime.utcnow())}}}
                transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_command)
                return Response(success=True).__dict__, 200


class Verify(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('transactionId', required=True, trim=True, type=non_empty_str, nullable=False,
                            help='transactionId is required')
        parser.add_argument('transactionRecordId', required=True, trim=True, type=non_empty_str, nullable=False,
                            help='transactionRecordId is required')
        args = parser.parse_args()
        transaction_record_id = args['transactionRecordId']
        transaction_record = transaction_db.transaction.find_one({"_id": ObjectId(transaction_record_id)})
        if transaction_record is None:
            raise TransactionRecordNotFound(transaction_record_id)
        transaction_verified = verify_wechat_transaction(args['transactionId'])
        update_query = {}
        if not transaction_verified:
            update_query['transactionState'] = TRANSACTION_STATE["failed"]
        else:
            update_query['transactionState'] = TRANSACTION_STATE["success"]
        transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, {'$set': update_query})
        transaction_record = transaction_db.transaction.find_one({"_id": ObjectId(transaction_record_id)})
        data = []
        if transaction_verified:
            transaction_record.update({'_id': str(transaction_record.get("_id"))})
            transaction_record.update({'merchandiseId': str(transaction_record.get("merchandiseId"))})
            transaction_record.update({'recipient': str(transaction_record.get("recipient"))})
            data.append(transaction_record)
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
        parser.add_argument('userEmail', required=True, trim=True, type=non_empty_str, nullable=False,
                            help='User email is required')
        parser.add_argument('merchandiseId', required=True, type=non_empty_str, nullable=False,
                            help='merchandiseId is required')
        parser.add_argument('paymentMethod', required=True, type=non_empty_str, nullable=False,
                            help='paymentMethod is required')
        args = parser.parse_args()
        user_email = args['userEmail']
        merchandise_id = args['merchandiseId']
        payment_method = args['paymentMethod']
        transaction = Transaction(user_email=user_email, merchandise_id=merchandise_id,
                                  payment_method=payment_method)
        return transaction.initiate_transaction()


class Transaction:
    user_email = None
    merchandise_id = None
    payment_method = None

    def __init__(self, user_email, merchandise_id, payment_method):
        self.user_email = user_email
        self.merchandise_id = merchandise_id
        self.payment_method = payment_method
        user_result = user_db.user.find_one({"email": user_email})
        merchandise_result = gym_db.merchandise.find_one({"_id": ObjectId(merchandise_id)})
        if user_result is None:
            raise TransactionUserNotFound(user_email)
        if merchandise_result is None:
            raise TransactionMerchandiseNotFound(merchandise_id)
        if payment_method not in SUPPORTED_PAYMENT_METHOD:
            raise TransactionPaymentMethodNotSupported(payment_method)
        pass

    def initiate_transaction(self):
        merchandise = gym_db.merchandise.find_one({"_id": ObjectId(self.merchandise_id)})
        prepay_id = self.request_wechat_payment()
        transaction = {"recipient": merchandise.get('owner'),
                       "payer": self.user_email,
                       "paymentMethod": self.payment_method,
                       "merchandiseId": merchandise.get('_id'),
                       "transactionState": TRANSACTION_STATE["pending"],
                       "createdDate": str(datetime.datetime.utcnow()),
                       "expiryInfo": merchandise.get('expiryInfo'),
                       "visitRecords": []
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


class TransactionRecord(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('Authorization', trim=True, type=bearer_header_str, nullable=False, location='headers', required=True, help='Needs to be logged in to view transaction records')
        args = parser.parse_args()
        token = args['Authorization']
        claim = jwt.decode(token=token, key=current_app.secret_key, algorithms='HS256',
                           options={'verify_exp': False})
        email = claim.get('user')
        current_app.logger.debug(email)
        gym_result = gym_db.gym.find_one({"email": email})
        user_result = user_db.gym.find_one({"email": email})
        results = []
        if user_result is not None:
            query = {'payer': email}
        elif gym_result is not None:
            query = {'recipient': gym_result.get('_id')}
        else:
            response = Response(success=False, data=[]).__dict__
            return response, 404
        raw_results = transaction_db.transaction.find(filter=query)
        for result in raw_results:
            result.update({'_id': str(result.get("_id"))})
            result.update({'merchandiseId': str(result.get("merchandiseId"))})
            result.update({'recipient': str(result.get("recipient"))})
            results.append(result)
        response = Response(success=True, data=results).__dict__
        return response, 200


transaction_api = Blueprint("transaction_api", __name__, url_prefix='/api/transaction')
transaction_api_router = Api(transaction_api)
transaction_api_router.add_resource(Initiate, '/initiate')
transaction_api_router.add_resource(Verify, '/verify')
transaction_api_router.add_resource(Cancel, '/cancel')
transaction_api_router.add_resource(Consume, '/consume')
transaction_api_router.add_resource(TransactionRecord, '/')
