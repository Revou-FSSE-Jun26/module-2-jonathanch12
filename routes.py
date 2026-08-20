from flask import Blueprint, jsonify, request
from app import db
from models import User, Product
from sqlalchemy.exc import IntegrityError
import bcrypt

# Main blueprint (general/utility routes)
main_bp = Blueprint('main', __name__)

# User blueprint
user_bp = Blueprint('user', __name__, url_prefix='/users')

# Auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Product blueprint
product_bp = Blueprint('product', __name__, url_prefix='/products')


# ==================== Main Routes ====================

# Database connection test
@main_bp.route('/')
def home():
    return jsonify({"message": "Connected to database successfully", "status": "ok"})


# ==================== User Routes ====================

# Register new user (POST)
@user_bp.route('/', methods=['POST'])
def register_user():
    data = request.get_json()
    try:
        for field in ['name', 'email', 'password', 'address']:
            if field not in data:
                return jsonify({"message": "Please fill missing fields", "status": "error"}), 400
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


# ==================== Auth Routes ====================

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

        return jsonify({"message": "Login successful", "user_id": user.id, "status": "ok"}), 200
    except Exception as e:
        print(f"Error logging in: {e}")
        return jsonify({"message": "Login error", "status": "error"}), 500


# ==================== Product Routes ====================

# Get all products (GET)
@product_bp.route('/', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products]), 200
    except Exception as e:
        return jsonify({"message": "Failed to get products", "status": "error"}), 500

# Get product's data by ID (GET)
@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        product = Product.query.get(product_id)
        if product:
            return jsonify(product.to_dict()), 200
        else:
            return jsonify({"message": "Product not found", "status": "not found"}), 404
    except Exception as e:
        return jsonify({"message": "Failed to get product by id", "status": "error"}), 500
