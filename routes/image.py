from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app import db
from models import Product, Image

# Image blueprint - nested under /products/<product_id>/images
image_bp = Blueprint('image', __name__, url_prefix='/products/<int:product_id>/images')


# Get all images for a product (GET)
@image_bp.route('/', methods=['GET'])
def get_product_images(product_id):
    try:
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({"message": "Product not found", "status": "not found"}), 404

        images = Image.query.filter_by(product_id=product_id, is_deleted=False).all()
        return jsonify({
            "images": [img.to_dict() for img in images],
            "status": "ok"
        }), 200
    except Exception as e:
        return jsonify({"message": "Failed to get images", "status": "error"}), 500


# Add one or more images to a product (POST) - Admin only
@image_bp.route('/', methods=['POST'])
@jwt_required()
def add_product_images(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    data = request.get_json()
    try:
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({"message": "Product not found", "status": "not found"}), 404

        # Accept both a single object {"url": "..."} and a list [{"url": "..."}, ...]
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = data
        else:
            return jsonify({"message": "Invalid request body", "status": "error"}), 400

        if len(items) == 0:
            return jsonify({"message": "No images provided", "status": "error"}), 400

        created_images = []
        for item in items:
            url = item.get('url') if isinstance(item, dict) else None
            if not url or not isinstance(url, str) or not url.strip():
                return jsonify({"message": "Each image must have a non-empty 'url' string", "status": "error"}), 400

            image = Image(product_id=product_id, url=url.strip())
            db.session.add(image)
            created_images.append(image)

        db.session.commit()
        return jsonify({
            "message": "Image(s) added successfully",
            "images": [img.to_dict() for img in created_images],
            "status": "ok"
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding images: {e}")
        return jsonify({"message": "Failed to add images", "status": "error"}), 500


# Update an image (PUT) - Admin only
@image_bp.route('/<int:image_id>', methods=['PUT'])
@jwt_required()
def update_product_image(product_id, image_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    data = request.get_json()
    try:
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({"message": "Product not found", "status": "not found"}), 404

        image = Image.query.get(image_id)
        if not image or image.is_deleted or image.product_id != product_id:
            return jsonify({"message": "Image not found", "status": "not found"}), 404

        url = data.get('url')
        if not url or not isinstance(url, str) or not url.strip():
            return jsonify({"message": "'url' must be a non-empty string", "status": "error"}), 400

        image.url = url.strip()
        db.session.commit()
        return jsonify({
            "message": "Image updated successfully",
            "image": image.to_dict(),
            "status": "ok"
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating image: {e}")
        return jsonify({"message": "Failed to update image", "status": "error"}), 500


# Soft-delete an image (DELETE) - Admin only
@image_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_product_image(product_id, image_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    try:
        product = Product.query.get(product_id)
        if not product or product.is_deleted:
            return jsonify({"message": "Product not found", "status": "not found"}), 404

        image = Image.query.get(image_id)
        if not image or image.is_deleted or image.product_id != product_id:
            return jsonify({"message": "Image not found", "status": "not found"}), 404

        from datetime import datetime
        image.is_deleted = True
        image.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Image deleted successfully", "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting image: {e}")
        return jsonify({"message": "Failed to delete image", "status": "error"}), 500
