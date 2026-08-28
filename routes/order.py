from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from models import User, Order

# Order blueprint
order_bp = Blueprint('order', __name__, url_prefix='/orders')


# Place a new order (POST) - Customer only
@order_bp.route('/', methods=['POST'])
@jwt_required()
def create_order():
    claims = get_jwt()
    if claims.get("role") != "customer":
        return jsonify({"message": "Customer access required", "status": "error"}), 403

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


# List all orders for a user (GET) - Customer only
@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    claims = get_jwt()
    if claims.get("role") != "customer":
        return jsonify({"message": "Customer access required", "status": "error"}), 403

    try:
        current_user_id = get_jwt_identity()
        orders = Order.query.filter_by(user_id=current_user_id, is_deleted=False).all()
        return jsonify([order.to_dict() for order in orders]), 200
    except Exception as e:
        return jsonify({"message": "Failed to get orders", "status": "error"}), 500


# View a specific order (GET) - Admin only
@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_by_id(order_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

    try:
        order = Order.query.get(order_id)
        if not order or order.is_deleted:
            return jsonify({"message": "Order not found", "status": "not found"}), 404

        return jsonify({"order": order.to_dict(), "status": "ok"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to get order", "status": "error"}), 500


# Delete an order - soft delete (DELETE) - Admin only
@order_bp.route('/<int:order_id>', methods=['DELETE'])
@jwt_required()
def delete_order(order_id):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"message": "Admin access required", "status": "error"}), 403

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
