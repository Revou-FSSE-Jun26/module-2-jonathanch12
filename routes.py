from flask import jsonify, request
from app import app, db
from models import User, Product
from sqlalchemy.exc import IntegrityError
import bcrypt

# Database connection test
@app.route('/')
def home():
    return jsonify({"message": "Connected to database successfully", "status": "ok"})

# Register new user (POST)
@app.route('/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    try:
        for field in ['name', 'email', 'password', 'address']:
            if field not in data:
                return jsonify({"message": "Please fill missing fields", "status": "error"}), 400
        user = User(
                    name=data.get('name'),
                    email=data.get('email'),
                    password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()),
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
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    try:
        user = User.query.get(user_id)
        if user:
            return jsonify({"message": "User found", "user": user.to_dict(), "status": "ok"}), 200
        else:
            return jsonify({"message": "User not found", "status": "ok"}), 404
    except Exception as e:
        return jsonify({"message": "Error getting user", "status": "error"}), 500

# Get all products (GET)
@app.route('/products', methods=['GET'])
def get_products():
    try:
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products]), 200
    except Exception as e:
        return jsonify({"message": "Failed to get products", "status": "error"}), 500

# Get product's data by ID (GET)
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        product = Product.query.get(product_id)
        if product:
            return jsonify(product.to_dict()), 200
        else:
            return jsonify({"message": "Product not found", "status": "not found"}), 404
    except Exception as e:
        return jsonify({"message": "Failed to get product by id", "status": "error"}), 500