# from flask import Flask, jsonify, request
# from flask_jwt_extended import (
#     JWTManager, jwt_required, create_access_token,
#     jwt_refresh_token_required, create_refresh_token,
#     get_jwt_identity, fresh_jwt_required
# )
#
# app = Flask(__name__)



# test1
#
# app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
# jwt = JWTManager(app)
#
#
# # Standard login endpoint. Will return a fresh access token and
# # a refresh token
# @app.route('/login', methods=['POST'])
# def login():
#     username = request.json.get('username', None)
#     password = request.json.get('password', None)
#     if username != 'test' or password != 'test':
#         return jsonify({"msg": "Bad username or password"}), 401
#
#     # create_access_token supports an optional 'fresh' argument,
#     # which marks the token as fresh or non-fresh accordingly.
#     # As we just verified their username and password, we are
#     # going to mark the token as fresh here.
#     ret = {
#         'access_token': create_access_token(identity=username, fresh=True),
#         'refresh_token': create_refresh_token(identity=username)
#     }
#     return jsonify(ret), 200
#
#
# # Refresh token endpoint. This will generate a new access token from
# # the refresh token, but will mark that access token as non-fresh,
# # as we do not actually verify a password in this endpoint.
# @app.route('/refresh', methods=['POST'])
# @jwt_refresh_token_required
# def refresh():
#     current_user = get_jwt_identity()
#     new_token = create_access_token(identity=current_user, fresh=False)
#     ret = {'access_token': new_token}
#     return jsonify(ret), 200
#
#
# # Fresh login endpoint. This is designed to be used if we need to
# # make a fresh token for a user (by verifying they have the
# # correct username and password). Unlike the standard login endpoint,
# # this will only return a new access token, so that we don't keep
# # generating new refresh tokens, which entirely defeats their point.
# @app.route('/fresh-login', methods=['POST'])
# def fresh_login():
#     username = request.json.get('username', None)
#     password = request.json.get('password', None)
#     if username != 'test' or password != 'test':
#         return jsonify({"msg": "Bad username or password"}), 401
#
#     new_token = create_access_token(identity=username, fresh=True)
#     ret = {'access_token': new_token}
#     return jsonify(ret), 200
#
#
# # Any valid JWT can access this endpoint
# @app.route('/protected', methods=['GET'])
# @jwt_required
# def protected():
#     username = get_jwt_identity()
#     return jsonify(logged_in_as=username), 200
#
#
# # Only fresh JWTs can access this endpoint
# @app.route('/protected-fresh', methods=['GET'])
# @fresh_jwt_required
# def protected_fresh():
#     username = get_jwt_identity()
#     return jsonify(fresh_logged_in_as=username), 200
#
#
# if __name__ == '__main__':
#     app.run()


from flask import Flask, request, jsonify

from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity,
    create_access_token, create_refresh_token,
    jwt_refresh_token_required, get_raw_jwt
)


# Setup flask
app = Flask(__name__)

# Enable blacklisting and specify what kind of tokens to check
# against the blacklist
app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
jwt = JWTManager(app)

# A storage engine to save revoked tokens. In production if
# speed is the primary concern, redis is a good bet. If data
# persistence is more important for you, postgres is another
# great option. In this example, we will be using an in memory
# store, just to show you how this might work. For more
# complete examples, check out these:
# https://github.com/vimalloc/flask-jwt-extended/blob/master/examples/redis_blacklist.py
# https://github.com/vimalloc/flask-jwt-extended/tree/master/examples/database_blacklist
blacklist = set()


# For this example, we are just checking if the tokens jti
# (unique identifier) is in the blacklist set. This could
# be made more complex, for example storing all tokens
# into the blacklist with a revoked status when created,
# and returning the revoked status in this call. This
# would allow you to have a list of all created tokens,
# and to consider tokens that aren't in the blacklist
# (aka tokens you didn't create) as revoked. These are
# just two options, and this can be tailored to whatever
# your application needs.
@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return jti in blacklist


# Standard login endpoint
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username != 'test' or password != 'test':
        return jsonify({"msg": "Bad username or password"}), 401

    ret = {
        'access_token': create_access_token(identity=username),
        'refresh_token': create_refresh_token(identity=username)
    }
    return jsonify(ret), 200


# Standard refresh endpoint. A blacklisted refresh token
# will not be able to access this endpoint
@app.route('/refresh', methods=['POST'])
@jwt_refresh_token_required
def refresh():
    current_user = get_jwt_identity()
    ret = {
        'access_token': create_access_token(identity=current_user)
    }
    return jsonify(ret), 200


# Endpoint for revoking the current users access token
@app.route('/logout', methods=['DELETE'])
@jwt_required
def logout():
    jti = get_raw_jwt()['jti']
    blacklist.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200


# Endpoint for revoking the current users refresh token
@app.route('/logout2', methods=['DELETE'])
@jwt_refresh_token_required
def logout2():
    jti = get_raw_jwt()['jti']
    blacklist.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200


# This will now prevent users with blacklisted tokens from
# accessing this endpoint
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    return jsonify({'hello': 'world'})

if __name__ == '__main__':
    app.run()