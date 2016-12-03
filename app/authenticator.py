from bson import ObjectId
from flask import current_app as app, jsonify, Blueprint
from flask_restful import Api, Resource
from flask_httpauth import HTTPTokenAuth, HTTPDigestAuth, MultiAuth
from jose import jwt, JWTError
import time_tools
from basic_response import Response, ErrorResponse
from exception import AuthenticationUserPasswordWrong, JWTNotVerified
from transaction import sanitize_transaction_record_result

auth_api = Blueprint('auth_api', __name__)
auth_api_router = Api(auth_api)

TNT_USER_AUTH_SCHEME = 'TNT-User-Auth'
WECHAT_USER_AUTH_SCHEME = 'Wechat-User-Auth'

TNT_GYM_AUTH_SCHEME = 'TNT-Gym-Auth'
WECHAT_Gym_AUTH_SCHEME = 'Wechat-Gym-Auth'

admin_token_auth = HTTPTokenAuth(scheme='tnt-admin-auth-scheme', realm='admin')
resource_access_auth = HTTPTokenAuth(scheme='Bearer', realm='resource')
user_auth = HTTPTokenAuth(scheme='Bearer', realm='user')
gym_auth = HTTPTokenAuth(scheme='Bearer', realm='gym')

user_login_pw_authenticator = HTTPDigestAuth(scheme=TNT_USER_AUTH_SCHEME, realm='user', use_ha1_pw=True)
user_login_authenticator = MultiAuth(main_auth=user_login_pw_authenticator)

gym_login_pw_authenticator = HTTPDigestAuth(scheme=TNT_GYM_AUTH_SCHEME, realm='gym', use_ha1_pw=True)

SESSION_TIMEOUT = 2628000

AUTHENTICATION_TYPE = ["password", "wechat"]
CLIENT_TYPE = {"gym": 1, "user": 2}


def authentication_method(auth_method):
    if auth_method is None or auth_method == "" or not isinstance(auth_method, dict) or auth_method.get(
            'type') is None or auth_method.get(
            'type') not in AUTHENTICATION_TYPE or auth_method.get('method') is None or auth_method.get('method') == "":
        raise ValueError('Authentication mal-formatted')
    else:
        return auth_method


@user_login_pw_authenticator.error_handler
def user_pw_auth_failed():
    return jsonify(ErrorResponse(AuthenticationUserPasswordWrong()).__dict__)


@gym_login_pw_authenticator.error_handler
def user_pw_auth_failed():
    return jsonify(ErrorResponse(AuthenticationUserPasswordWrong()).__dict__)


@user_auth.error_handler
def user_jwt_auth_failed():
    return jsonify(ErrorResponse(JWTNotVerified()).__dict__)


@gym_auth.error_handler
def gym_jwt_auth_failed():
    return jsonify(ErrorResponse(JWTNotVerified()).__dict__)

# @admin_token_auth.verify_token
# def verify_token(token):
#     username, password = base64.decodestring(token).split(':')
#     user = db.user.find_one(filter={"username": username})
#     if user is None:
#         app.logger.error("user %s not found", username)
#         return False
#     return sha256_crypt.verify(password, user['hashed_password'])


@gym_auth.verify_token
def verify_token(token):
    try:
        from flask import current_app
        claim = jwt.decode(token=token, key=app.secret_key, algorithms='HS512', options={'verify_exp': False})
        current_app.logger.debug(claim)
        if claim.get('type') and claim.get('id') and claim.get('type') == CLIENT_TYPE["gym"]:
            from database import gym_db as db
            current_app.logger.debug("is gym jwt")
            gym = db.gym.find_one({"_id": ObjectId(claim.get('id'))})
            if not gym:
                return False
            else:
                return True
        return False
    except JWTError as e:
        app.logger.error("jwt not verified: %s", type(e).__name__)
        return False


@user_auth.verify_token
def verify_token(token):
    try:
        from flask import current_app

        claim = jwt.decode(token=token, key=app.secret_key, algorithms='HS512', options={'verify_exp': False})
        current_app.logger.debug(claim)

        if claim.get('type') and claim.get('id') and claim.get('type') == CLIENT_TYPE["user"]:
            from database import user_db as db
            current_app.logger.debug("is user jwt")

            user = db.user.find_one({"_id": ObjectId(claim.get('id'))})
            if not user:
                return False
            else:
                return True
        return False
    except JWTError as e:
        app.logger.error("jwt not verified: %s", type(e).__name__)
        return False


class UserAuthToken(Resource):
    @user_login_authenticator.login_required
    def get(self):
        from database import user_db as db
        import user as api
        username = user_login_pw_authenticator.username()
        user = db.user.find_one({'username': username})
        transaction_records = []
        from database import transaction_db
        raw_results = transaction_db.transaction.find(filter={'payer': user['email']})
        for result in raw_results:
            transaction_records.append(sanitize_transaction_record_result(result))
        issued_time = time_tools.get_current_time_second()
        claims = {'iat': issued_time, 'id': str(user['_id']), 'type': CLIENT_TYPE["user"]}
        return Response(success=True, data={'jwt': jwt.encode(claims=claims, key=app.secret_key, algorithm='HS512'),
                                            'user': api.sanitize_user_return_data(user), 'transactionRecords': transaction_records}).__dict__, 200


class GymAuthToken(Resource):
    @gym_login_pw_authenticator.login_required
    def get(self):
        from database import gym_db as db
        import gym as api
        gym_email = gym_login_pw_authenticator.username()
        gym = db.gym.find_one({'email': gym_email})
        merchandises = []
        raw_results = db.merchandise.find(filter={'owner': gym['_id']}, limit=20)
        for result in raw_results:
            merchandises.append(api.sanitize_merchandise_return_data(result))
        issued_time = time_tools.get_current_time_second()

        claims = {'iat': issued_time, 'id': str(gym['_id']), 'type': CLIENT_TYPE["gym"]}
        return Response(success=True, data={'jwt': jwt.encode(claims=claims, key=app.secret_key, algorithm='HS512'),
                                            'gym': api.sanitize_gym_return_data(gym), 'merchandises': merchandises}).__dict__, 200


# class AdminAuthToken(Resource):
#     @admin_token_auth.login_required
#     def post(self):
#         args = request.get_json()
#         auth_type, token = request.headers['Authorization'].split(
#             None, 1)
#         username, password = base64.decodestring(token).split(':')
#         if args.get('username') is None:
#             return make_response('username missing in payload', 400)
#         issued_time = timegm(datetime.utcnow().utctimetuple())
#         claims = {'exp': issued_time + SESSION_TIMEOUT, 'iat': issued_time, 'user': username, 'level': USER_LEVEL['Admin']}
#         return jwt.encode(claims=claims, key=app.secret_key, algorithm='HS256')


class WechatAuthToken(Resource):
    def post(self):
        pass


auth_api_router.add_resource(UserAuthToken, '/api/login/user')
auth_api_router.add_resource(GymAuthToken, '/api/login/gym')
