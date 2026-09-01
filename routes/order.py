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


# List all orders for a user (GET) and all existing orders for admin (GET) - Customer and Admin only
@order_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    claims = get_jwt()
    role = claims.get("role")

    if role not in ("customer", "admin"):
        return jsonify({"message": "Customer or admin access required", "status": "error"}), 403

    try:
        if role == "customer":  # List all orders for the logged-in customer
            current_user_id = int(get_jwt_identity())
            orders = Order.query.filter_by(user_id=current_user_id, is_deleted=False).all()
        else:  # role == "admin" - list all orders
            orders = Order.query.filter_by(is_deleted=False).all()

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


# Update an order status (PUT) - Admin (forward-only flow) and Customer (cancel own pending order)
VALID_STATUSES = ['pending', 'processing', 'delivering', 'completed', 'cancelled']

# Allowed forward-only status transitions for admin
ALLOWED_TRANSITIONS = {
    'pending':    ['processing', 'cancelled'],
    'processing': ['delivering', 'cancelled'],
    'delivering': ['completed', 'cancelled'],
    'completed':  [],
    'cancelled':  [],
}

@order_bp.route('/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    claims = get_jwt()
    role = claims.get("role")

    if role not in ("customer", "admin"):
        return jsonify({"message": "Customer or admin access required", "status": "error"}), 403

    data = request.get_json()
    try:
        if 'status' not in data:
            return jsonify({"message": "Please provide a status", "status": "error"}), 400

        new_status = data['status']
        if new_status not in VALID_STATUSES:
            return jsonify({
                "message": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
                "status": "error"
            }), 400

        order = Order.query.get(order_id)
        if not order or order.is_deleted:
            return jsonify({"message": "Order not found", "status": "not found"}), 404

        # Cannot change status of an already completed or cancelled order
        if order.status in ('completed', 'cancelled'):
            return jsonify({
                "message": f"Cannot update an order that is already {order.status}",
                "status": "error"
            }), 409

        if role == "customer":
            current_user_id = int(get_jwt_identity())
            # Customers can only update their own orders
            if order.user_id != current_user_id:
                return jsonify({"message": "You can only update your own orders", "status": "error"}), 403

            # Customers can only cancel
            if new_status != "cancelled":
                return jsonify({"message": "Customers can only cancel their orders", "status": "error"}), 403

            # Customers can only cancel while the order is still pending
            if order.status != "pending":
                return jsonify({
                    "message": f"Cannot cancel an order that is currently {order.status}",
                    "status": "error"
                }), 409
        else:  # role == "admin" - enforce forward-only status flow
            if new_status not in ALLOWED_TRANSITIONS[order.status]:
                return jsonify({
                    "message": f"Cannot change status from '{order.status}' to '{new_status}'. Allowed: {', '.join(ALLOWED_TRANSITIONS[order.status]) or 'none'}",
                    "status": "error"
                }), 409

        # If the order is being cancelled, restock the products
        if new_status == "cancelled":
            items = db.session.query(order_items).filter(order_items.c.order_id == order.id).all()
            for item in items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity

        order.status = new_status
        db.session.commit()
        return jsonify({"message": "Order updated successfully", "order": order.to_dict(), "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating order: {e}")
        return jsonify({"message": "Failed to update order", "status": "error"}), 500


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
