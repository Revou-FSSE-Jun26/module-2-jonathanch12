from flask import Blueprint, jsonify, request
from app import db
from models import User
from sqlalchemy.exc import IntegrityError
import bcrypt

# User blueprint
user_bp = Blueprint('user', __name__, url_prefix='/users')


# Validation function for user registration fields
def validate_registration_data(data):
    # Name must be a string
    if not isinstance(data['name'], str):
        return jsonify({"message": "Validation error", "error": "Name must be a string", "status": "error"}), 400

    # Password must be 8 characters or longer
    if len(data['password']) < 8:
        return jsonify({"message": "Validation error", "error": "Password must be at least 8 characters", "status": "error"}), 400

    return None


# Register new user (POST)
@user_bp.route('/', methods=['POST'])
def register_user():
    data = request.get_json()
    try:
        for field in ['name', 'email', 'password', 'address']:
            if field not in data:
                return jsonify({"message": "Please fill missing fields", "status": "error"}), 400

        # Validate registration fields
        validation_error = validate_registration_data(data)
        if validation_error:
            return validation_error

        user = User(
                    name=data.get('name'),
                    email=data.get('email'),
                    password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
                    address = data.get('address')
                )
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User registration successfull", "user": user.to_dict(), "status": "ok"}), 201
    except IntegrityError:
        print("Please use another email")
        db.session.rollback()
        return jsonify({"message": "Please use another email", "status": "error"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error registering user: {e}")
        return jsonify({"message": "User registration error", "status": "error"}), 500


# Get user's data by ID (GET)
@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            return jsonify({"message": "User found", "user": user.to_dict(), "status": "ok"}), 200
        else:
            return jsonify({"message": "User not found", "status": "ok"}), 404
    except Exception as e:
        return jsonify({"message": "Error getting user", "status": "error"}), 500
