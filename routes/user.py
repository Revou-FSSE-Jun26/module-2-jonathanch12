from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
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

    # Phone must be a string
    if not isinstance(data['phone'], str):
        return jsonify({"message": "Validation error", "error": "Phone must be a string", "status": "error"}), 400

    # Password must be 8 characters or longer
    if len(data['password']) < 8:
        return jsonify({"message": "Validation error", "error": "Password must be at least 8 characters", "status": "error"}), 400

    return None


# Register new user (POST)
@user_bp.route('/', methods=['POST'])
def register_user():
    data = request.get_json()
    try:
        for field in ['name', 'email', 'phone', 'password', 'address']:
            if field not in data:
                return jsonify({"message": "Please fill missing fields", "status": "error"}), 400

        # Validate registration fields
        validation_error = validate_registration_data(data)
        if validation_error:
            return validation_error

        user = User(
                    name=data.get('name'),
                    email=data.get('email'),
                    phone=data.get('phone'),
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

# View user's data (GET)
@user_bp.route('/', methods=['GET'])
@jwt_required()
def get_user_data():
    try:
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"message": "User not found", "status": "error"}), 404
        return jsonify({"message": "Displaying user's data", "user": user.to_dict(), "status": "ok"}), 200
    except Exception as e:
        print(f"Error retrieving user data: {e}")
        return jsonify({"message": "User data retrieval error", "status": "error"}), 500


# Fields a user is allowed to update
UPDATABLE_FIELDS = ['name', 'password', 'phone', 'address']


# Validation function for user update fields
def validate_update_data(data):
    # Reject any field that is not allowed to be updated
    disallowed = [field for field in data if field not in UPDATABLE_FIELDS]
    if disallowed:
        return jsonify({
            "message": "Validation error",
            "error": f"The following fields cannot be updated: {', '.join(disallowed)}",
            "status": "error"
        }), 400

    # Name must be a non-empty string
    if 'name' in data:
        if not isinstance(data['name'], str):
            return jsonify({"message": "Validation error", "error": "Name must be a string", "status": "error"}), 400
        if not data['name'].strip():
            return jsonify({"message": "Validation error", "error": "Name must not be empty", "status": "error"}), 400

    # Phone must be a non-empty string
    if 'phone' in data:
        if not isinstance(data['phone'], str):
            return jsonify({"message": "Validation error", "error": "Phone must be a string", "status": "error"}), 400
        if not data['phone'].strip():
            return jsonify({"message": "Validation error", "error": "Phone must not be empty", "status": "error"}), 400

    # Address must be a non-empty string
    if 'address' in data:
        if not isinstance(data['address'], str):
            return jsonify({"message": "Validation error", "error": "Address must be a string", "status": "error"}), 400
        if not data['address'].strip():
            return jsonify({"message": "Validation error", "error": "Address must not be empty", "status": "error"}), 400

    # Password must be a non-empty string of at least 8 characters
    if 'password' in data:
        if not isinstance(data['password'], str):
            return jsonify({"message": "Validation error", "error": "Password must be a string", "status": "error"}), 400
        if not data['password'].strip():
            return jsonify({"message": "Validation error", "error": "Password must not be empty", "status": "error"}), 400
        if len(data['password']) < 8:
            return jsonify({"message": "Validation error", "error": "Password must be at least 8 characters", "status": "error"}), 400

    return None


# Update user's data (PUT)
@user_bp.route('/', methods=['PUT'])
@jwt_required()
def update_user_data():
    data = request.get_json()
    try:
        if not data:
            return jsonify({"message": "Please provide fields to update", "status": "error"}), 400

        # Validate update fields
        validation_error = validate_update_data(data)
        if validation_error:
            return validation_error

        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"message": "User not found", "status": "error"}), 404

        # Apply updates only for fields present in the request body
        if 'name' in data:
            user.name = data['name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'address' in data:
            user.address = data['address']
        if 'password' in data:
            user.password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        db.session.commit()
        return jsonify({"message": "User data updated successfully", "user": user.to_dict(), "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating user data: {e}")
        return jsonify({"message": "User data update error", "status": "error"}), 500
