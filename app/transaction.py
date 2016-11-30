from bson import ObjectId
from flask import Blueprint, current_app as app
from flask_restful import Api, reqparse, Resource
from jose import jwt

import time_tools
from authenticator import CLIENT_TYPE
from basic_response import Response
from database import transaction_db, gym_db, user_db
from exception import TransactionPaymentMethodNotSupported, \
    TransactionUserNotFound, TransactionMerchandiseNotFound, TransactionRecordNotFound, TransactionRecordInvalidState, \
    TransactionRecordExpired, TransactionRecordCountUsedUp
from gym import EXPIRY_INFO_TYPE
from utils import bearer_header_str, non_empty_str
from authenticator import gym_auth

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
        if transaction_record.get('transactionState') == TRANSACTION_STATE["expired"]:
            raise TransactionRecordExpired(transaction_record_id)
        if transaction_record.get('transactionState') != TRANSACTION_STATE["success"]:
            raise TransactionRecordInvalidState(transaction_record_id, transaction_record.get('transactionState'))
        if transaction_record.get('expiryInfo').get('type') == EXPIRY_INFO_TYPE["by_count"]:
            exp_date = time_tools.to_second(transaction_record.get('expiryInfo').get('expiryDate'))
            from flask import current_app as app
            app.logger.debug(exp_date)
            if exp_date != "" and time_tools.is_expired(exp_date):
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
                update_command = {'$set': update_query, '$push': {'visitRecords': {'date': time_tools.get_current_time()}}}
                transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_command)
                return Response(success=True).__dict__, 200
        elif transaction_record.get('expiryInfo').get('type') == EXPIRY_INFO_TYPE["by_duration"]:
            start_date = transaction_record.get('createdDate')
            expiry_date = time_tools.to_second(start_date) + transaction_record.get(
                'expiryInfo').get('duration')
            if time_tools.is_expired(expiry_date):
                update_query = {'transactionState': TRANSACTION_STATE["expired"]}
                update_command = {'$set': update_query}
                transaction_db.transaction.update_one({"_id": ObjectId(transaction_record_id)}, update_command)
                raise TransactionRecordExpired(transaction_record_id)
            else:
                update_command = {'$push': {'visitRecords': {'date': time_tools.get_current_time()}}}
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
            data.append(sanitize_transaction_record_result(transaction_record))
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
                       "createdDate": time_tools.get_current_time(),
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


class TransactionRecord(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('merchandiseId', location='args', type=ObjectId, nullable=False, trim=True)
        parser.add_argument('find', location='args', type=int, nullable=False, trim=True)
        parser.add_argument('Authorization', trim=True, type=bearer_header_str, nullable=False, location='headers', required=True, help='Needs to be logged in to view transaction records')
        args = parser.parse_args()
        token = args['Authorization']
        claim = jwt.decode(token=token, key=app.secret_key, algorithms='HS512',
                           options={'verify_exp': False})
        target_id = claim.get('id')
        client_type = claim.get('type')
        results = []
        query = {}
        if client_type == CLIENT_TYPE["user"]:
            user_result = user_db.user.find_one({"_id": ObjectId(target_id)})
            owner_query = {'payer': user_result['email']}
        elif client_type == CLIENT_TYPE["gym"]:
            owner_query = {'recipient': ObjectId(target_id)}
        else:
            response = Response(success=False, data=[]).__dict__
            return response, 404
        if args.get('merchandiseId'):
            query['$and'] = [owner_query, {'merchandiseId': args.get('merchandiseId')}]
        else:
            query = owner_query
        limit = args['find'] if args['find'] is not None else 0
        raw_results = transaction_db.transaction.find(filter=query, limit=limit)
        for result in raw_results:
            results.append(sanitize_transaction_record_result(result))
        response = Response(success=True, data=results).__dict__
        return response, 200


class TransactionRecordAnalysis(Resource):

    @gym_auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('merchandiseId', type=ObjectId, nullable=False, trim=True)
        parser.add_argument('range', type=long, nullable=False, trim=True, required=True)
        parser.add_argument('Authorization', trim=True, type=bearer_header_str, nullable=False, location='headers',
                            required=True, help='Needs to be logged in to view transaction records')
        args = parser.parse_args()
        token = args['Authorization']
        claim = jwt.decode(token=token, key=app.secret_key, algorithms='HS512',
                           options={'verify_exp': False})
        target_id = claim.get('id')
        prev_start = time_tools.get_days_before_current(args.get('range') * 2)
        prev_end = time_tools.get_days_before_current(args.get('range'))
        results = []
        if args.get('merchandiseId'):
            current_query = {'$and': [{'createdDate': {'$lt': time_tools.get_current_time(), '$gte': prev_end}}, {'recipient': ObjectId(target_id)}, {'merchandiseId': args.get('merchandiseId')}]}
            prev_query = {'$and': [{'createdDate': {'$lt': prev_end, '$gte': prev_start}}, {'recipient': ObjectId(target_id)}, {'merchandiseId': args.get('merchandiseId')}]}
            prev_sales = transaction_db.transaction.find(filter=prev_query).count()
            current_sales = transaction_db.transaction.find(filter=current_query).count()
            merchandise_result = gym_db.merchandise.find_one({"_id": args.get('merchandiseId')})
            if prev_sales == 0:
                percent_dif = 0
            else:
                percent_dif = (current_sales - prev_sales) / prev_sales * 100
            from gym import sanitize_merchandise_return_data
            results.append({'percent': percent_dif, 'merchandise': sanitize_merchandise_return_data(merchandise_result)})
        else:
            raw_results = gym_db.merchandise.find(filter={'owner': ObjectId(target_id)})
            for result in raw_results:
                current_query = {'$and': [{'createdDate': {'$lt': time_tools.get_current_time(), '$gte': prev_end}},
                                          {'recipient': ObjectId(target_id)}, {'merchandiseId': result.get('_id')}]}
                prev_query = {
                    '$and': [{'createdDate': {'$lt': prev_end, '$gte': prev_start}}, {'recipient': ObjectId(target_id)},
                             {'merchandiseId': result.get('_id')}]}
                prev_sales = transaction_db.transaction.find(filter=prev_query).count()
                current_sales = transaction_db.transaction.find(filter=current_query).count()
                if prev_sales == 0:
                    percent_dif = 0
                else:
                    percent_dif = (current_sales - prev_sales) / prev_sales * 100
                from gym import sanitize_merchandise_return_data
                results.append(
                    {'percent': percent_dif, 'merchandise': sanitize_merchandise_return_data(result)})
        response = Response(success=True, data=results).__dict__
        return response, 200


def sanitize_transaction_record_result(transaction_record):
    transaction_record.update({'_id': str(transaction_record.get("_id"))})
    transaction_record.update({'merchandiseId': str(transaction_record.get("merchandiseId"))})
    transaction_record.update({'recipient': str(transaction_record.get("recipient"))})
    transaction_record.update({'createdDate': transaction_record.get('createdDate').isoformat()})
    expiry_info = transaction_record.get('expiryInfo')
    if expiry_info.get('type') == EXPIRY_INFO_TYPE["by_count"]:
        if expiry_info.get('startDate') != "":
            start_date_iso = expiry_info.get('startDate').isoformat()
            expiry_info.update({'startDate': start_date_iso})
        if expiry_info.get('expiryDate') != "":
            exp_date_iso = expiry_info.get('expiryDate').isoformat()
            expiry_info.update({'expiryDate': exp_date_iso})
            transaction_record.update({'expiryInfo': expiry_info})
    visit_records = []
    for visit_record in transaction_record.get('visitRecords'):
        visit = visit_record.get('date')
        visit_record.update({'date': visit.isoformat()})
        visit_records.append(visit_record)
    transaction_record.update({'visitRecords': visit_records})
    return transaction_record

transaction_api = Blueprint("transaction_api", __name__, url_prefix='/api/transaction')
transaction_api_router = Api(transaction_api)
transaction_api_router.add_resource(Initiate, '/initiate')
transaction_api_router.add_resource(Verify, '/verify')
transaction_api_router.add_resource(Cancel, '/cancel')
transaction_api_router.add_resource(Consume, '/consume')
transaction_api_router.add_resource(TransactionRecord, '/')
transaction_api_router.add_resource(TransactionRecordAnalysis, '/analysis')

