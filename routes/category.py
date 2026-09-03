from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from models import Product, Category
from sqlalchemy.exc import IntegrityError

# Category blueprint
category_bp = Blueprint('category', __name__, url_prefix='/categories')


# Create new category (POST) - Admin only
@category_bp.route('/', methods=['POST'])
@jwt_required()
def create_category():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

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

        products = Product.query.filter_by(category_id=category_id, is_deleted=False).all()
        result = category.to_dict()
        result['products'] = [product.to_dict() for product in products]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": "Failed to get category", "status": "error"}), 500


# Update category (PUT) - Admin only
@category_bp.route('/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

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


# Delete category - soft delete (DELETE) - Admin only
@category_bp.route('/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

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
