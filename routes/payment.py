from datetime import datetime

import midtransclient
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app import db
from models import Order, Payment

# Payment blueprint. No url_prefix because it serves both /payments/* and
# /orders/<id>/payments routes.
payment_bp = Blueprint('payment', __name__)

# Midtrans transaction_status values that mean the order has been paid for.
PAID_STATUSES = ('settlement', 'capture')


def _build_snap_client():
    """Create a Midtrans Snap client from app config."""
    return midtransclient.Snap(
        is_production=current_app.config.get('MIDTRANS_IS_PRODUCTION', False),
        server_key=current_app.config.get('MIDTRANS_SERVER_KEY'),
        client_key=current_app.config.get('MIDTRANS_CLIENT_KEY'),
    )


def _build_core_client():
    """Create a Midtrans Core API client (used to verify notifications)."""
    return midtransclient.CoreApi(
        is_production=current_app.config.get('MIDTRANS_IS_PRODUCTION', False),
        server_key=current_app.config.get('MIDTRANS_SERVER_KEY'),
        client_key=current_app.config.get('MIDTRANS_CLIENT_KEY'),
    )


def _apply_order_effect(order, transaction_status, fraud_status):
    """Advance the order based on a verified payment status.

    Per the plan (section 6): a successful payment auto-advances a still-pending
    order to 'processing'. All other statuses leave the order untouched so the
    customer can retry.
    """
    is_paid = (
        transaction_status == 'settlement'
        or (transaction_status == 'capture' and fraud_status == 'accept')
    )
    if is_paid and order is not None and order.status == 'pending' and not order.is_deleted:
        order.status = 'processing'


# Create a payment for one of the customer's own orders (POST) - Customer only
@payment_bp.route('/payments', methods=['POST'])
@jwt_required()
def create_payment():
    claims = get_jwt()
    if claims.get("role") != "customer":
        return jsonify({"message": "Customer access required", "status": "error"}), 403

    data = request.get_json(silent=True) or {}
    try:
        order_id = data.get('order_id')
        if order_id is None or not isinstance(order_id, int):
            return jsonify({"message": "Please provide a valid integer order_id", "status": "error"}), 400

        order = Order.query.get(order_id)
        if not order or order.is_deleted:
            return jsonify({"message": "Order not found", "status": "not found"}), 404

        # Customers can only pay for their own orders
        current_user_id = int(get_jwt_identity())
        if order.user_id != current_user_id:
            return jsonify({"message": "You can only pay for your own orders", "status": "error"}), 403

        # Only unpaid, pending orders can be paid for
        if order.status != 'pending':
            return jsonify({
                "message": f"Cannot pay for an order that is currently {order.status}",
                "status": "error"
            }), 409

        # Amount is always taken from the order's total_amount (never the client)
        amount = order.total_amount

        # Create the payment row first so we have its id for a globally unique
        # Midtrans order id (supports retries / payment history per order).
        payment = Payment(order_id=order.id, amount=amount, status='pending')
        db.session.add(payment)
        db.session.flush()  # assigns payment.id without committing

        payment.midtrans_order_id = f"order-{order.id}-{payment.id}-live"

        # Midtrans expects gross_amount as an integer (IDR has no decimals)
        gross_amount = int(round(float(amount)))

        snap = _build_snap_client()
        frontend_url = current_app.config["FRONTEND_URL"]
        snap_param = {
            "transaction_details": {
                "order_id": payment.midtrans_order_id,
                "gross_amount": gross_amount,
            },
            "customer_details": {
                "first_name": order.user.name,
                "email": order.user.email,
                "phone": order.user.phone,
            },
            "callbacks": {
                "finish": f"{frontend_url}/orders/{order.id}",
            },
        }

        transaction = snap.create_transaction(snap_param)

        db.session.commit()
        return jsonify({
            "message": "Payment created successfully",
            "payment": payment.to_dict(),
            "snap_token": transaction.get('token'),
            "redirect_url": transaction.get('redirect_url'),
            "status": "ok"
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error creating payment: {e}")
        return jsonify({"message": "Failed to create payment", "status": "error"}), 500


# Midtrans HTTP notification / webhook (POST) - PUBLIC (no JWT)
@payment_bp.route('/payments/notification', methods=['POST'])
def payment_notification():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"message": "Invalid notification body", "status": "error"}), 400

    try:
        # Verify the notification with Midtrans. The client re-fetches the
        # authoritative status by transaction_id rather than trusting the body.
        core = _build_core_client()
        status_response = core.transactions.notification(body)

        midtrans_order_id = status_response.get('order_id')
        transaction_status = status_response.get('transaction_status')
        fraud_status = status_response.get('fraud_status')
        payment_type = status_response.get('payment_type')
        transaction_id = status_response.get('transaction_id')
        signature_key = status_response.get('signature_key')

        if not midtrans_order_id:
            return jsonify({"message": "Missing order_id in notification", "status": "error"}), 400

        # Find the exact payment attempt by the id we sent to Midtrans
        payment = Payment.query.filter_by(midtrans_order_id=midtrans_order_id).first()
        if not payment:
            return jsonify({"message": "Payment not found", "status": "not found"}), 404

        # Update the payment row from the verified response
        payment.status = transaction_status or payment.status
        if payment_type:
            payment.method = payment_type
        if transaction_id:
            payment.transaction_id = transaction_id
        if signature_key:
            payment.signature_key = signature_key
        payment.updated_at = datetime.utcnow()

        # Apply the order-side effect (auto-advance to processing when paid)
        order = Order.query.get(payment.order_id)
        _apply_order_effect(order, transaction_status, fraud_status)

        db.session.commit()
        return jsonify({"message": "Notification processed", "status": "ok"}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error processing payment notification: {e}")
        return jsonify({"message": "Failed to process notification", "status": "error"}), 500


# View a specific payment (GET) - Admin (any) and Customer (own only)
@payment_bp.route('/payments/<int:payment_id>', methods=['GET'])
@jwt_required()
def get_payment_by_id(payment_id):
    claims = get_jwt()
    role = claims.get("role")

    if role not in ("customer", "admin"):
        return jsonify({"message": "Customer or admin access required", "status": "error"}), 403

    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"message": "Payment not found", "status": "not found"}), 404

        if role == "customer":
            current_user_id = int(get_jwt_identity())
            if payment.order.user_id != current_user_id:
                return jsonify({"message": "You can only view your own payments", "status": "error"}), 403

        return jsonify({"payment": payment.to_dict(), "status": "ok"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to get payment", "status": "error"}), 500


# List all payment attempts for an order (GET) - Admin (any) and Customer (own only)
@payment_bp.route('/orders/<int:order_id>/payments', methods=['GET'])
@jwt_required()
def get_order_payments(order_id):
    claims = get_jwt()
    role = claims.get("role")

    if role not in ("customer", "admin"):
        return jsonify({"message": "Customer or admin access required", "status": "error"}), 403

    try:
        order = Order.query.get(order_id)
        if not order or order.is_deleted:
            return jsonify({"message": "Order not found", "status": "not found"}), 404

        if role == "customer":
            current_user_id = int(get_jwt_identity())
            if order.user_id != current_user_id:
                return jsonify({"message": "You can only view your own orders", "status": "error"}), 403

        payments = (
            Payment.query
            .filter_by(order_id=order_id)
            .order_by(Payment.created_at.desc())
            .all()
        )
        return jsonify({
            "payments": [p.to_dict() for p in payments],
            "status": "ok"
        }), 200
    except Exception as e:
        return jsonify({"message": "Failed to get payments", "status": "error"}), 500
