from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from app import db
from models import User, Order, Product, order_items

# Fixed number of orders returned per page
ORDERS_PER_PAGE = 20

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

    # Base query: never expose soft-deleted orders
    query = Order.query.filter_by(is_deleted=False)

    # ---- Role-based user scoping ----
    user_id_param = request.args.get("user_id")
    if role == "customer":
        # The user_id filter is reserved for admins only
        if user_id_param is not None:
            return jsonify({
                "message": "The user_id filter is only available to admins",
                "status": "error"
            }), 403
        current_user_id = int(get_jwt_identity())
        query = query.filter(Order.user_id == current_user_id)
    else:  # role == "admin" - may optionally filter by a specific user
        if user_id_param is not None:
            try:
                user_id_value = int(user_id_param)
            except (TypeError, ValueError):
                return jsonify({"message": "user_id must be an integer", "status": "error"}), 400
            query = query.filter(Order.user_id == user_id_value)

    # ---- status filter ----
    status = request.args.get("status")
    if status is not None:
        if status not in VALID_STATUSES:
            return jsonify({
                "message": f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
                "status": "error"
            }), 400
        query = query.filter(Order.status == status)

    # ---- amount range filter ----
    min_amount_param = request.args.get("min_amount")
    max_amount_param = request.args.get("max_amount")
    min_amount = None
    max_amount = None

    if min_amount_param is not None:
        try:
            min_amount = float(min_amount_param)
        except (TypeError, ValueError):
            return jsonify({"message": "min_amount must be a number", "status": "error"}), 400
        if min_amount < 0:
            return jsonify({"message": "min_amount cannot be negative", "status": "error"}), 400

    if max_amount_param is not None:
        try:
            max_amount = float(max_amount_param)
        except (TypeError, ValueError):
            return jsonify({"message": "max_amount must be a number", "status": "error"}), 400
        if max_amount < 0:
            return jsonify({"message": "max_amount cannot be negative", "status": "error"}), 400

    if min_amount is not None and max_amount is not None and max_amount < min_amount:
        return jsonify({
            "message": "max_amount cannot be less than min_amount",
            "status": "error"
        }), 400

    if min_amount is not None:
        query = query.filter(Order.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Order.total_amount <= max_amount)

    # ---- date range filter (created_at), YYYY-MM-DD, both inclusive ----
    start_date_param = request.args.get("start_date")
    end_date_param = request.args.get("end_date")

    if start_date_param is not None:
        try:
            start_date = datetime.strptime(start_date_param, "%Y-%m-%d")
        except (TypeError, ValueError):
            return jsonify({"message": "start_date must be in YYYY-MM-DD format", "status": "error"}), 400
        query = query.filter(Order.created_at >= start_date)

    if end_date_param is not None:
        try:
            end_date = datetime.strptime(end_date_param, "%Y-%m-%d")
        except (TypeError, ValueError):
            return jsonify({"message": "end_date must be in YYYY-MM-DD format", "status": "error"}), 400
        # Inclusive of the entire end day
        query = query.filter(Order.created_at < end_date + timedelta(days=1))

    # ---- product_id filter (orders containing the given product) ----
    product_id_param = request.args.get("product_id")
    if product_id_param is not None:
        try:
            product_id_value = int(product_id_param)
        except (TypeError, ValueError):
            return jsonify({"message": "product_id must be an integer", "status": "error"}), 400
        query = query.filter(
            Order.id.in_(
                db.session.query(order_items.c.order_id).filter(
                    order_items.c.product_id == product_id_value
                )
            )
        )

    # ---- pagination (fixed 20 items per page) ----
    page_param = request.args.get("page", "1")
    try:
        page = int(page_param)
    except (TypeError, ValueError):
        return jsonify({"message": "page must be an integer", "status": "error"}), 400
    if page < 1:
        return jsonify({"message": "page must be a positive integer", "status": "error"}), 400

    try:
        query = query.order_by(Order.created_at.desc())
        pagination = query.paginate(page=page, per_page=ORDERS_PER_PAGE, error_out=False)

        return jsonify({
            "orders": [order.to_dict() for order in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total_items": pagination.total,
                "total_pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev
            },
            "status": "ok"
        }), 200
    except Exception as e:
        return jsonify({"message": "Failed to get orders", "status": "error"}), 500


# View a specific order (GET) - Admin (any order) and Customer (own order only)
@order_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_by_id(order_id):
    claims = get_jwt()
    role = claims.get("role")

    if role not in ("customer", "admin"):
        return jsonify({"message": "Customer or admin access required", "status": "error"}), 403

    try:
        order = Order.query.get(order_id)
        if not order or order.is_deleted:
            return jsonify({"message": "Order not found", "status": "not found"}), 404

        # Customers may only view their own orders
        if role == "customer":
            current_user_id = int(get_jwt_identity())
            if order.user_id != current_user_id:
                return jsonify({"message": "You can only view your own orders", "status": "error"}), 403

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

        order.is_deleted = True
        order.deleted_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Order deleted successfully", "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting order: {e}")
        return jsonify({"message": "Failed to delete order", "status": "error"}), 500
