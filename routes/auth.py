from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token
from models import User
import bcrypt

# Auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


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
            "status": "ok"
        }), 200
    except Exception as e:
        print(f"Error logging in: {e}")
        return jsonify({"message": "Login error", "status": "error"}), 500
