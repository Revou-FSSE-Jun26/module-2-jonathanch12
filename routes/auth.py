from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
)
from models import User
from datetime import timedelta
import bcrypt

# Auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _access_token_expires_in():
    """Return the access token lifetime in whole seconds.

    Reads JWT_ACCESS_TOKEN_EXPIRES so the value stays in sync with app config.
    Handles both timedelta and plain-int/float configurations.
    """
    expires = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES")
    if isinstance(expires, timedelta):
        return int(expires.total_seconds())
    return int(expires)


# Login user (POST)
@auth_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    try:
        if 'email' not in data or 'password' not in data:
            return jsonify({"message": "Please provide email and password", "status": "error"}), 400

        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({"message": "Invalid email or password", "status": "error"}), 401

        if isinstance(user.password, bytes):
            hashed_password = user.password
        else:
            hashed_password = user.password.encode('utf-8')

        if not bcrypt.checkpw(data['password'].encode('utf-8'), hashed_password):
            return jsonify({"message": "Invalid email or password", "status": "error"}), 401

        # Create JWT tokens with user role as additional claim
        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

        return jsonify({
            "message": "Login successful",
            "name": user.name,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": _access_token_expires_in(),
            "status": "ok"
        }), 200
    except Exception as e:
        print(f"Error logging in: {e}")
        return jsonify({"message": "Login error", "status": "error"}), 500


# Refresh access token (POST)
# Requires a valid refresh token in the Authorization header:
#   Authorization: Bearer <refresh_token>
# Issues a new short-lived access token, re-attaching the user's role claim.
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        identity = get_jwt_identity()
        role = get_jwt().get("role")
        access_token = create_access_token(
            identity=identity,
            additional_claims={"role": role}
        )
        return jsonify({
            "access_token": access_token,
            "expires_in": _access_token_expires_in(),
            "status": "ok"
        }), 200
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return jsonify({"message": "Token refresh error", "status": "error"}), 500
