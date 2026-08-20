from flask import Blueprint, jsonify, request
from app import db
from models import User, Product, Category, Order, order_items
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

# Category blueprint
category_bp = Blueprint('category', __name__, url_prefix='/categories')

# Order blueprint
order_bp = Blueprint('order', __name__, url_prefix='/orders')


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

# Create new product (POST)
@product_bp.route('/', methods=['POST'])
def create_product():
    data = request.get_json()
    try:
        for field in ['category_id', 'name', 'description', 'price', 'stock']:
            if field not in data:
                return jsonify({"message": "Please fill missing fields", "status": "error"}), 400

        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({"message": "Category not found", "status": "error"}), 404

        product = Product(
            category_id=data['category_id'],
            name=data['name'],
            description=data['description'],
            price=data['price'],
            stock=data['stock']
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product created successfully", "product": product.to_dict(), "status": "ok"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating product: {e}")
        return jsonify({"message": "Failed to create product", "status": "error"}), 500

# Update existing product (PUT)
@product_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.get_json()
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": "Product not found", "status": "not found"}), 404

        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({"message": "Category not found", "status": "error"}), 404
            product.category_id = data['category_id']

        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'stock' in data:
            product.stock = data['stock']

        db.session.commit()
        return jsonify({"message": "Product updated successfully", "product": product.to_dict(), "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating product: {e}")
        return jsonify({"message": "Failed to update product", "status": "error"}), 500

# Delete existing product (DELETE)
@product_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": "Product not found", "status": "not found"}), 404

        # Check if product has active orders
        exists = db.session.query(order_items).filter(order_items.c.product_id == product_id).first()
        if exists:
            return jsonify({"message": "Cannot delete product with active orders", "status": "error"}), 409

        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully", "status": "ok"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Cannot delete product with active orders", "status": "error"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {e}")
        return jsonify({"message": "Failed to delete product", "status": "error"}), 500


# ==================== Category Routes ====================

# Create new category (POST)
@category_bp.route('/', methods=['POST'])
def create_category():
    data = request.get_json()
    try:
        if 'name' not in data:
            return jsonify({"message": "Please fill missing fields", "status": "error"}), 400

        category = Category(
            name=data['name'],
            description=data.get('description')
        )
        db.session.add(category)
        db.session.commit()
        return jsonify({"message": "Category created successfully", "category": category.to_dict(), "status": "ok"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Category name already exists", "status": "error"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error creating category: {e}")
        return jsonify({"message": "Failed to create category", "status": "error"}), 500

# Get all categories (GET)
@category_bp.route('/', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.filter_by(is_deleted=False).all()
        return jsonify([category.to_dict() for category in categories]), 200
    except Exception as e:
        return jsonify({"message": "Failed to get categories", "status": "error"}), 500

# Get category by ID with its products (GET)
@category_bp.route('/<int:category_id>', methods=['GET'])
def get_category_by_id(category_id):
    try:
        category = Category.query.get(category_id)
        if not category or category.is_deleted:
            return jsonify({"message": "Category not found", "status": "not found"}), 404

        products = Product.query.filter_by(category_id=category_id).all()
        result = category.to_dict()
        result['products'] = [product.to_dict() for product in products]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": "Failed to get category", "status": "error"}), 500

# Update category (PUT)
@category_bp.route('/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    data = request.get_json()
    try:
        category = Category.query.get(category_id)
        if not category or category.is_deleted:
            return jsonify({"message": "Category not found", "status": "not found"}), 404

        if 'name' in data:
            category.name = data['name']
        if 'description' in data:
            category.description = data['description']

        db.session.commit()
        return jsonify({"message": "Category updated successfully", "category": category.to_dict(), "status": "ok"}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Category name already exists", "status": "error"}), 409
    except Exception as e:
        db.session.rollback()
        print(f"Error updating category: {e}")
        return jsonify({"message": "Failed to update category", "status": "error"}), 500

# Delete category - soft delete (DELETE)
@category_bp.route('/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        category = Category.query.get(category_id)
        if not category or category.is_deleted:
            return jsonify({"message": "Category not found", "status": "not found"}), 404

        # Check if category has products linked to it
        products = Product.query.filter_by(category_id=category_id).first()
        if products:
            return jsonify({"message": "Cannot delete category with existing products", "status": "error"}), 409

        from datetime import datetime
        category.is_deleted = True
        category.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Category deleted successfully", "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting category: {e}")
        return jsonify({"message": "Failed to delete category", "status": "error"}), 500


# ==================== Order Routes ====================

# Place a new order (POST)
@order_bp.route('/', methods=['POST'])
def create_order():
    data = request.get_json()
    try:
        for field in ['user_id', 'total_amount']:
            if field not in data:
                return jsonify({"message": "Please fill missing fields", "status": "error"}), 400

        user = User.query.get(data['user_id'])
        if not user:
            return jsonify({"message": "User not found", "status": "error"}), 404

        order = Order(
            user_id=data['user_id'],
            total_amount=data['total_amount']
        )
        db.session.add(order)
        db.session.commit()
        return jsonify({"message": "Order created successfully", "order": order.to_dict(), "status": "ok"}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {e}")
        return jsonify({"message": "Failed to create order", "status": "error"}), 500

# List all orders for a user (GET)
@order_bp.route('/', methods=['GET'])
def get_orders():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"message": "Please provide user_id", "status": "error"}), 400

        orders = Order.query.filter_by(user_id=user_id, is_deleted=False).all()
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        return jsonify({"message": "Failed to get orders", "status": "error"}), 500

# View a specific order (GET)
@order_bp.route('/<int:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    try:
        order = Order.query.get(order_id)
        if not order or order.is_deleted:
            return jsonify({"message": "Order not found", "status": "not found"}), 404

        return jsonify({"order": order.to_dict(), "status": "ok"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to get order", "status": "error"}), 500

# Delete an order - soft delete (DELETE)
@order_bp.route('/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        order = Order.query.get(order_id)
        if not order or order.is_deleted:
            return jsonify({"message": "Order not found", "status": "not found"}), 404

        if order.status in ['delivering', 'processing']:
            return jsonify({"message": "Cannot delete order that is currently " + order.status, "status": "error"}), 409

        from datetime import datetime
        order.is_deleted = True
        order.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Order deleted successfully", "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting order: {e}")
        return jsonify({"message": "Failed to delete order", "status": "error"}), 500
