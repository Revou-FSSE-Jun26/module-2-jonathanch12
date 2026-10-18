from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from datetime import datetime
from app import db
from models import Product, Image
from helper.cloudinary_service import (
    upload_image,
    destroy_image,
    CloudinaryServiceError,
)

# Image blueprint - nested under /products/<product_id>/images
image_bp = Blueprint('image', __name__, url_prefix='/products/<int:product_id>/images')


def _collect_upload_sources():
    """Gather image sources from the request.

    Supports two input styles:
      - multipart/form-data file upload(s) under the "file" field (one or many)
      - JSON body with a single {"url": "..."} object or a list of them

    Returns a tuple (sources, error_response).
    Each source is a dict: {"type": "file"|"url", "value": <stream|url>}.
    When validation fails, sources is None and error_response is a
    (json, status) tuple ready to be returned by the caller.
    """
    sources = []

    # 1) File uploads (multipart/form-data)
    files = request.files.getlist('file')
    files = [f for f in files if f and f.filename]
    for f in files:
        sources.append({"type": "file", "value": f})

    # 2) JSON URL(s) - only parse when no files were sent, or alongside them
    if request.is_json:
        data = request.get_json(silent=True)
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = data
        elif data is None:
            items = []
        else:
            return None, (jsonify({"message": "Invalid request body", "status": "error"}), 400)

        for item in items:
            url = item.get('url') if isinstance(item, dict) else None
            if not url or not isinstance(url, str) or not url.strip():
                return None, (jsonify({
                    "message": "Each image must have a non-empty 'url' string",
                    "status": "error"
                }), 400)
            sources.append({"type": "url", "value": url.strip()})

    if len(sources) == 0:
        return None, (jsonify({"message": "No images provided", "status": "error"}), 400)

    return sources, None


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
# Accepts either uploaded files (multipart/form-data "file" field) or JSON
# {"url": "..."} / a list of them. Files and URLs are uploaded to Cloudinary;
# only the returned secure URL and public_id are stored in the database.
@image_bp.route('/', methods=['POST'])
@jwt_required()
def add_product_images(product_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    product = Product.query.get(product_id)
    if not product or product.is_deleted:
        return jsonify({"message": "Product not found", "status": "not found"}), 404

    sources, error = _collect_upload_sources()
    if error is not None:
        return error

    uploaded_public_ids = []  # track for cleanup if the DB commit fails
    created_images = []
    try:
        for source in sources:
            secure_url, public_id = upload_image(source["value"], product_id)
            uploaded_public_ids.append(public_id)

            image = Image(product_id=product_id, url=secure_url, public_id=public_id)
            db.session.add(image)
            created_images.append(image)

        db.session.commit()
        return jsonify({
            "message": "Image(s) added successfully",
            "images": [img.to_dict() for img in created_images],
            "status": "ok"
        }), 201

    except CloudinaryServiceError as e:
        # An upload failed partway through. Roll back the DB and remove any
        # assets that did make it to Cloudinary so nothing is orphaned.
        db.session.rollback()
        _cleanup_uploaded(uploaded_public_ids)
        print(f"Cloudinary error adding images: {e}")
        return jsonify({"message": "Failed to upload image(s) to Cloudinary", "status": "error"}), 502

    except Exception as e:
        db.session.rollback()
        _cleanup_uploaded(uploaded_public_ids)
        print(f"Error adding images: {e}")
        return jsonify({"message": "Failed to add images", "status": "error"}), 500


# Update/replace an image (PUT) - Admin only
# Uploads the new file or URL to Cloudinary, replacing the old asset in place
# (reusing the existing public_id so the old file is overwritten), then updates
# the stored URL.
@image_bp.route('/<int:image_id>', methods=['PUT'])
@jwt_required()
def update_product_image(product_id, image_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    product = Product.query.get(product_id)
    if not product or product.is_deleted:
        return jsonify({"message": "Product not found", "status": "not found"}), 404

    image = Image.query.get(image_id)
    if not image or image.is_deleted or image.product_id != product_id:
        return jsonify({"message": "Image not found", "status": "not found"}), 404

    sources, error = _collect_upload_sources()
    if error is not None:
        return error
    if len(sources) != 1:
        return jsonify({"message": "Provide exactly one image to replace with", "status": "error"}), 400

    source = sources[0]
    old_public_id = image.public_id
    try:
        if old_public_id:
            # Overwrite the existing asset in place; keeps the same public_id.
            secure_url, new_public_id = upload_image(
                source["value"], product_id, public_id=old_public_id
            )
        else:
            # Legacy row with no Cloudinary asset: upload fresh.
            secure_url, new_public_id = upload_image(source["value"], product_id)

        image.url = secure_url
        image.public_id = new_public_id
        db.session.commit()
        return jsonify({
            "message": "Image updated successfully",
            "image": image.to_dict(),
            "status": "ok"
        }), 200

    except CloudinaryServiceError as e:
        db.session.rollback()
        print(f"Cloudinary error updating image: {e}")
        return jsonify({"message": "Failed to upload image to Cloudinary", "status": "error"}), 502

    except Exception as e:
        db.session.rollback()
        print(f"Error updating image: {e}")
        return jsonify({"message": "Failed to update image", "status": "error"}), 500


# Soft-delete an image (DELETE) - Admin only
# Removes the asset from Cloudinary first; if that fails the whole request
# fails and the database row is left untouched.
@image_bp.route('/<int:image_id>', methods=['DELETE'])
@jwt_required()
def delete_product_image(product_id, image_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    product = Product.query.get(product_id)
    if not product or product.is_deleted:
        return jsonify({"message": "Product not found", "status": "not found"}), 404

    image = Image.query.get(image_id)
    if not image or image.is_deleted or image.product_id != product_id:
        return jsonify({"message": "Image not found", "status": "not found"}), 404

    # Remove from Cloudinary first. A failure here fails the entire request.
    if image.public_id:
        try:
            destroy_image(image.public_id)
        except CloudinaryServiceError as e:
            print(f"Cloudinary error deleting image: {e}")
            return jsonify({
                "message": "Failed to delete image from Cloudinary",
                "status": "error"
            }), 502

    try:
        image.is_deleted = True
        image.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Image deleted successfully", "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting image: {e}")
        return jsonify({"message": "Failed to delete image", "status": "error"}), 500


def _cleanup_uploaded(public_ids):
    """Best-effort removal of assets uploaded during a failed POST batch."""
    for pid in public_ids:
        try:
            destroy_image(pid)
        except CloudinaryServiceError as e:
            print(f"Cleanup failed for {pid}: {e}")
