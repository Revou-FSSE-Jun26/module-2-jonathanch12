from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from models import User, Order, Product, order_items

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
        if 'order_items' not in data or not isinstance(data['order_items'], list) or len(data['order_items']) == 0:
            return jsonify({"message": "Please provide at least one order item", "status": "error"}), 400

        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"message": "User not found", "status": "error"}), 404

        # Validate each order item and calculate total_amount
        total_amount = 0
        items_to_insert = []

        for item in data['order_items']:
            if 'product_id' not in item or 'quantity' not in item:
                return jsonify({"message": "Each order item must have product_id and quantity", "status": "error"}), 400

            if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
                return jsonify({"message": "Quantity must be a positive integer", "status": "error"}), 400

            product = Product.query.get(item['product_id'])
            if not product or product.is_deleted:
                return jsonify({"message": f"Product with id {item['product_id']} not found", "status": "error"}), 404

            # Check stock availability
            if product.stock < item['quantity']:
                return jsonify({
                    "message": f"Insufficient stock for product '{product.name}'. Available: {product.stock}, Requested: {item['quantity']}",
                    "status": "error"
                }), 409

            unit_price = float(product.price)
            total_amount += unit_price * item['quantity']

            items_to_insert.append({
                "product_id": item['product_id'],
                "quantity": item['quantity'],
                "unit_price": unit_price,
                "product": product
            })
        print(current_user_id)
        # Create the order
        order = Order(
            user_id=current_user_id,
            total_amount=total_amount
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID without committing

        # Insert order items and reduce stock
        for item_data in items_to_insert:
            db.session.execute(order_items.insert().values(
                order_id=order.id,
                product_id=item_data['product_id'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price']
            ))
            # Reduce product stock
            item_data['product'].stock -= item_data['quantity']

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
        current_user_id = int(get_jwt_identity())
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
