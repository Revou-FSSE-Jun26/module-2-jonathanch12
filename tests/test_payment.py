import pytest
from unittest.mock import MagicMock, patch
from flask_jwt_extended import create_access_token
from app import db
from models import User, Order, Payment
from tests._helpers import auth


@pytest.fixture
def customer_user(app):
    """Create a customer user and return their data and token."""
    with app.app_context():
        user = User(name="Customer", email="customer@test.com", phone="1234567890",
                    password="hashed", address="123 St", role="customer")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"role": "customer"})
        return {"id": user.id, "token": token}


@pytest.fixture
def other_customer(app):
    """Create a second customer (used to test cross-user access)."""
    with app.app_context():
        user = User(name="Other Customer", email="other@test.com", phone="5555555555",
                    password="hashed", address="456 Ave", role="customer")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"role": "customer"})
        return {"id": user.id, "token": token}


@pytest.fixture
def admin_user(app):
    """Create an admin user and return their data and token."""
    with app.app_context():
        user = User(name="Admin", email="admin@test.com", phone="0987654321",
                    password="hashed", address="1 Admin Rd", role="admin")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"role": "admin"})
        return {"id": user.id, "token": token}


def _make_order(user_id, total_amount=199000, status="pending", is_deleted=False):
    """Helper to persist an order and return its id."""
    order = Order(user_id=user_id, total_amount=total_amount, status=status, is_deleted=is_deleted)
    db.session.add(order)
    db.session.commit()
    return order.id


def _make_payment(order_id, amount=199000, status="pending", midtrans_order_id=None):
    """Helper to persist a payment and return its id."""
    payment = Payment(order_id=order_id, amount=amount, status=status,
                      midtrans_order_id=midtrans_order_id)
    db.session.add(payment)
    db.session.commit()
    return payment.id


@pytest.fixture
def mock_snap():
    """Patch the Midtrans Snap client so no real HTTP call is made."""
    with patch("routes.payment.midtransclient") as mock_mt:
        snap_instance = MagicMock()
        snap_instance.create_transaction.return_value = {
            "token": "fake-snap-token",
            "redirect_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/fake",
        }
        mock_mt.Snap.return_value = snap_instance
        yield mock_mt


class TestCreatePayment:
    """POST /payments - Customer only. A customer may only pay for their own order."""

    def test_customer_creates_payment_for_own_order(self, app, client, customer_user, mock_snap):
        """Customer can create a payment for their own pending order."""
        with app.app_context():
            order_id = _make_order(customer_user["id"], total_amount=199000)

        response = client.post('/payments', json={"order_id": order_id},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 201
        assert data["message"] == "Payment created successfully"
        assert data["status"] == "ok"
        assert data["snap_token"] == "fake-snap-token"
        assert data["redirect_url"].startswith("https://app.sandbox.midtrans.com")
        assert data["payment"]["order_id"] == order_id
        assert data["payment"]["amount"] == 199000
        assert data["payment"]["status"] == "pending"

    def test_amount_taken_from_order_not_client(self, app, client, customer_user, mock_snap):
        """Payment amount comes from the order's total_amount, ignoring any client-supplied amount."""
        with app.app_context():
            order_id = _make_order(customer_user["id"], total_amount=500000)

        response = client.post('/payments', json={"order_id": order_id, "amount": 1},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 201
        assert data["payment"]["amount"] == 500000

    def test_payment_row_persisted_with_midtrans_order_id(self, app, client, customer_user, mock_snap):
        """A payment row is stored with the per-attempt midtrans_order_id (order-<order>-<payment>)."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])

        response = client.post('/payments', json={"order_id": order_id},
            headers=auth(client, customer_user['token']))
        payment_id = response.get_json()["payment"]["id"]

        with app.app_context():
            payment = Payment.query.get(payment_id)
            assert payment is not None
            assert payment.midtrans_order_id == f"order-{order_id}-{payment_id}"

    def test_customer_cannot_pay_for_other_users_order(self, app, client, customer_user, other_customer, mock_snap):
        """A customer cannot create a payment for an order owned by another user (403)."""
        with app.app_context():
            # Order belongs to other_customer
            order_id = _make_order(other_customer["id"])

        response = client.post('/payments', json={"order_id": order_id},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "You can only pay for your own orders"

    def test_customer_pay_for_other_users_order_creates_no_payment(self, app, client, customer_user, other_customer, mock_snap):
        """A rejected cross-user payment attempt must not create any payment row."""
        with app.app_context():
            order_id = _make_order(other_customer["id"])

        client.post('/payments', json={"order_id": order_id},
            headers=auth(client, customer_user['token']))

        with app.app_context():
            assert Payment.query.count() == 0

    def test_payment_order_not_found(self, client, customer_user, mock_snap):
        """Paying for a non-existent order returns 404."""
        response = client.post('/payments', json={"order_id": 9999},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Order not found"

    def test_payment_soft_deleted_order_not_found(self, app, client, customer_user, mock_snap):
        """Paying for a soft-deleted order returns 404."""
        with app.app_context():
            order_id = _make_order(customer_user["id"], is_deleted=True)

        response = client.post('/payments', json={"order_id": order_id},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Order not found"

    def test_payment_order_not_pending(self, app, client, customer_user, mock_snap):
        """Paying for an order that is no longer pending returns 409."""
        with app.app_context():
            order_id = _make_order(customer_user["id"], status="processing")

        response = client.post('/payments', json={"order_id": order_id},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 409
        assert "Cannot pay for an order that is currently processing" in data["message"]

    def test_payment_missing_order_id(self, client, customer_user, mock_snap):
        """Missing order_id returns 400."""
        response = client.post('/payments', json={},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 400
        assert "order_id" in data["message"]

    def test_payment_invalid_order_id_type(self, client, customer_user, mock_snap):
        """A non-integer order_id returns 400."""
        response = client.post('/payments', json={"order_id": "abc"},
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 400
        assert "order_id" in data["message"]

    # ---- Access control ----

    def test_public_user_cannot_create_payment(self, client, mock_snap):
        """A public (not logged in) user cannot access the create-payment route (401)."""
        response = client.post('/payments', json={"order_id": 1})

        assert response.status_code == 401

    def test_admin_cannot_create_payment(self, app, client, admin_user, customer_user, mock_snap):
        """Only customers may create payments; admin is forbidden (403)."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])

        response = client.post('/payments', json={"order_id": order_id},
            headers=auth(client, admin_user['token']))
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Customer access required"


class TestGetPaymentById:
    """GET /payments/<id> - Admin (any) and Customer (own only). Public users forbidden."""

    def test_customer_views_own_payment(self, app, client, customer_user):
        """A customer can view a payment belonging to their own order."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])
            payment_id = _make_payment(order_id)

        response = client.get(f'/payments/{payment_id}',
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "ok"
        assert data["payment"]["id"] == payment_id
        assert data["payment"]["order_id"] == order_id

    def test_customer_cannot_view_other_users_payment(self, app, client, customer_user, other_customer):
        """A customer cannot view a payment that belongs to another user's order (403)."""
        with app.app_context():
            order_id = _make_order(other_customer["id"])
            payment_id = _make_payment(order_id)

        response = client.get(f'/payments/{payment_id}',
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "You can only view your own payments"

    def test_admin_views_any_payment(self, app, client, admin_user, customer_user):
        """An admin can view any payment."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])
            payment_id = _make_payment(order_id)

        response = client.get(f'/payments/{payment_id}',
            headers=auth(client, admin_user['token']))
        data = response.get_json()

        assert response.status_code == 200
        assert data["payment"]["id"] == payment_id

    def test_payment_not_found(self, client, admin_user):
        """Fetching a non-existent payment returns 404."""
        response = client.get('/payments/9999',
            headers=auth(client, admin_user['token']))
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Payment not found"

    def test_public_user_cannot_view_payment(self, app, client, customer_user):
        """A public (not logged in) user cannot view a payment (401)."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])
            payment_id = _make_payment(order_id)

        response = client.get(f'/payments/{payment_id}')

        assert response.status_code == 401

    def test_unknown_role_cannot_view_payment(self, app, client, customer_user):
        """A token with an unknown role cannot view a payment (403)."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])
            payment_id = _make_payment(order_id)
            token = create_access_token(identity="99", additional_claims={"role": "guest"})

        response = client.get(f'/payments/{payment_id}',
            headers=auth(client, token))
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Customer or admin access required"


class TestGetOrderPayments:
    """GET /orders/<id>/payments - Admin (any) and Customer (own only). Public users forbidden."""

    def test_customer_lists_own_order_payments(self, app, client, customer_user):
        """A customer can list all payment attempts for their own order."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])
            _make_payment(order_id, status="deny", midtrans_order_id="a")
            _make_payment(order_id, status="pending", midtrans_order_id="b")

        response = client.get(f'/orders/{order_id}/payments',
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "ok"
        assert len(data["payments"]) == 2

    def test_customer_cannot_list_other_users_order_payments(self, app, client, customer_user, other_customer):
        """A customer cannot list payments for another user's order (403)."""
        with app.app_context():
            order_id = _make_order(other_customer["id"])
            _make_payment(order_id)

        response = client.get(f'/orders/{order_id}/payments',
            headers=auth(client, customer_user['token']))
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "You can only view your own orders"

    def test_admin_lists_any_order_payments(self, app, client, admin_user, customer_user):
        """An admin can list payments for any order."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])
            _make_payment(order_id)

        response = client.get(f'/orders/{order_id}/payments',
            headers=auth(client, admin_user['token']))
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["payments"]) == 1

    def test_list_payments_order_not_found(self, client, admin_user):
        """Listing payments for a non-existent order returns 404."""
        response = client.get('/orders/9999/payments',
            headers=auth(client, admin_user['token']))
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Order not found"

    def test_public_user_cannot_list_order_payments(self, app, client, customer_user):
        """A public (not logged in) user cannot list order payments (401)."""
        with app.app_context():
            order_id = _make_order(customer_user["id"])

        response = client.get(f'/orders/{order_id}/payments')

        assert response.status_code == 401


class TestPaymentNotification:
    """POST /payments/notification - public webhook, verified server-side via Midtrans."""

    def test_settlement_updates_payment_and_advances_order(self, app, client, customer_user):
        """A settlement notification marks the payment paid and advances a pending order to processing."""
        with app.app_context():
            order_id = _make_order(customer_user["id"], status="pending")
            payment_id = _make_payment(order_id, status="pending", midtrans_order_id="order-X-1")

        verified = {
            "order_id": "order-X-1",
            "transaction_status": "settlement",
            "fraud_status": "accept",
            "payment_type": "bank_transfer",
            "transaction_id": "txn-123",
            "signature_key": "sig-abc",
        }
        with patch("routes.payment.midtransclient") as mock_mt:
            core_instance = MagicMock()
            core_instance.transactions.notification.return_value = verified
            mock_mt.CoreApi.return_value = core_instance

            response = client.post('/payments/notification', json=verified)

        assert response.status_code == 200

        with app.app_context():
            payment = Payment.query.get(payment_id)
            assert payment.status == "settlement"
            assert payment.method == "bank_transfer"
            assert payment.transaction_id == "txn-123"
            assert payment.signature_key == "sig-abc"
            order = Order.query.get(order_id)
            assert order.status == "processing"

    def test_pending_notification_leaves_order_pending(self, app, client, customer_user):
        """A pending notification updates the payment but does not advance the order."""
        with app.app_context():
            order_id = _make_order(customer_user["id"], status="pending")
            payment_id = _make_payment(order_id, status="pending", midtrans_order_id="order-Y-1")

        verified = {
            "order_id": "order-Y-1",
            "transaction_status": "pending",
            "fraud_status": "accept",
            "payment_type": "gopay",
            "transaction_id": "txn-456",
        }
        with patch("routes.payment.midtransclient") as mock_mt:
            core_instance = MagicMock()
            core_instance.transactions.notification.return_value = verified
            mock_mt.CoreApi.return_value = core_instance

            response = client.post('/payments/notification', json=verified)

        assert response.status_code == 200
        with app.app_context():
            assert Payment.query.get(payment_id).status == "pending"
            assert Order.query.get(order_id).status == "pending"

    def test_notification_unknown_order_id_returns_404(self, app, client):
        """A notification for an unknown midtrans_order_id returns 404."""
        verified = {
            "order_id": "order-does-not-exist",
            "transaction_status": "settlement",
            "fraud_status": "accept",
            "transaction_id": "txn-x",
        }
        with patch("routes.payment.midtransclient") as mock_mt:
            core_instance = MagicMock()
            core_instance.transactions.notification.return_value = verified
            mock_mt.CoreApi.return_value = core_instance

            response = client.post('/payments/notification', json=verified)
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Payment not found"

    def test_notification_invalid_body(self, client):
        """A non-JSON-object body returns 400."""
        response = client.post('/payments/notification', json="not-a-dict")
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Invalid notification body"
