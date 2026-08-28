from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from models import Product, Category, order_items

# Product blueprint
product_bp = Blueprint('product', __name__, url_prefix='/products')


# Get all products (GET)
@product_bp.route('/', methods=['GET'])
def get_products():
    try:
        products = Product.query.filter_by(is_deleted=False).all()
        return jsonify([product.to_dict() for product in products]), 200
    except Exception as e:
        return jsonify({"message": "Failed to get products", "status": "error"}), 500


# Get product's data by ID (GET)
@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({"message": "Product not found", "status": "not found"}), 404
        return jsonify(product.to_dict()), 200
    except Exception as e:
        return jsonify({"message": "Failed to get product by id", "status": "error"}), 500


# Create new product (POST) - Admin only
@product_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

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


# Update existing product (PUT) - Admin only
@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    data = request.get_json()
    try:
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
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


# Delete existing product - soft delete (DELETE) - Admin only
@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    try:
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({"message": "Product not found", "status": "not found"}), 404

        # Check if product has active orders
        exists = db.session.query(order_items).filter(order_items.c.product_id == product_id).first()
        if exists:
            return jsonify({"message": "Cannot delete product with active orders", "status": "error"}), 409

        from datetime import datetime
        product.is_deleted = True
        product.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Product deleted successfully", "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {e}")
        return jsonify({"message": "Failed to delete product", "status": "error"}), 500
