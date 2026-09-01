import pytest
from flask_jwt_extended import create_access_token
from app import db
from models import User, Category, Product, Order, order_items


@pytest.fixture
def customer_user(app):
    """Create a customer user and return their data and token."""
    with app.app_context():
        user = User(name="Customer", email="customer@test.com", password="hashed", address="123 St", role="customer")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"role": "customer"})
        return {"id": user.id, "token": token}


@pytest.fixture
def admin_user(app):
    """Create an admin user and return their data and token."""
    with app.app_context():
        user = User(name="Admin", email="admin@test.com", password="hashed", address="1 Admin Rd", role="admin")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"role": "admin"})
        return {"id": user.id, "token": token}


@pytest.fixture
def sample_products(app):
    """Create sample category and products for order tests."""
    with app.app_context():
        category = Category(name="Electronics", description="Gadgets")
        db.session.add(category)
        db.session.commit()

        p1 = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
        p2 = Product(category_id=category.id, name="Keyboard", description="RGB", price=799000, stock=25)
        db.session.add_all([p1, p2])
        db.session.commit()
        return [{"id": p1.id, "price": 199000, "stock": 50}, {"id": p2.id, "price": 799000, "stock": 25}]


class TestCreateOrder:
    """Test cases for POST /orders/ - Customer only"""

    def test_customer_creates_order_successfully(self, app, client, customer_user, sample_products):
        """Test customer can create an order with calculated total_amount."""
        response = client.post('/orders/', json={
            "order_items": [
                {"product_id": sample_products[0]["id"], "quantity": 2}
            ]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 201
        assert data["message"] == "Order created successfully"
        assert data["order"]["total_amount"] == 199000 * 2
        assert data["order"]["status"] == "pending"
        assert data["status"] == "ok"

    def test_stock_reduced_after_order(self, app, client, customer_user, sample_products):
        """Test product stock is reduced after order creation."""
        client.post('/orders/', json={
            "order_items": [
                {"product_id": sample_products[0]["id"], "quantity": 3}
            ]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})

        with app.app_context():
            product = Product.query.get(sample_products[0]["id"])
            assert product.stock == 50 - 3

    def test_order_with_multiple_items(self, app, client, customer_user, sample_products):
        """Test order with multiple items calculates total correctly."""
        response = client.post('/orders/', json={
            "order_items": [
                {"product_id": sample_products[0]["id"], "quantity": 2},
                {"product_id": sample_products[1]["id"], "quantity": 1}
            ]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        expected_total = (199000 * 2) + (799000 * 1)
        assert response.status_code == 201
        assert data["order"]["total_amount"] == expected_total

    def test_create_order_missing_order_items(self, client, customer_user):
        """Test creating order without order_items returns 400."""
        response = client.post('/orders/', json={},
            headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide at least one order item"

    def test_create_order_empty_order_items(self, client, customer_user):
        """Test creating order with empty order_items list returns 400."""
        response = client.post('/orders/', json={
            "order_items": []
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide at least one order item"

    def test_create_order_item_missing_product_id(self, client, customer_user):
        """Test order item without product_id returns 400."""
        response = client.post('/orders/', json={
            "order_items": [{"quantity": 2}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Each order item must have product_id and quantity"

    def test_create_order_item_missing_quantity(self, client, customer_user, sample_products):
        """Test order item without quantity returns 400."""
        response = client.post('/orders/', json={
            "order_items": [{"product_id": sample_products[0]["id"]}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Each order item must have product_id and quantity"

    def test_create_order_quantity_not_positive(self, client, customer_user, sample_products):
        """Test order item with zero or negative quantity returns 400."""
        response = client.post('/orders/', json={
            "order_items": [{"product_id": sample_products[0]["id"], "quantity": 0}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Quantity must be a positive integer"

    def test_create_order_product_not_found(self, client, customer_user):
        """Test ordering non-existent product returns 404."""
        response = client.post('/orders/', json={
            "order_items": [{"product_id": 999, "quantity": 1}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 404
        assert "not found" in data["message"]

    def test_create_order_soft_deleted_product(self, app, client, customer_user):
        """Test ordering soft-deleted product returns 404."""
        with app.app_context():
            category = Category(name="Books", description="Reading")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Deleted Book", description="Gone",
                            price=100000, stock=10, is_deleted=True)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.post('/orders/', json={
            "order_items": [{"product_id": prod_id, "quantity": 1}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 404
        assert "not found" in data["message"]

    def test_create_order_insufficient_stock(self, client, customer_user, sample_products):
        """Test ordering more than available stock returns 409."""
        response = client.post('/orders/', json={
            "order_items": [{"product_id": sample_products[0]["id"], "quantity": 9999}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "Insufficient stock" in data["message"]

    def test_create_order_no_token(self, client):
        """Test creating order without token returns 401."""
        response = client.post('/orders/', json={
            "order_items": [{"product_id": 1, "quantity": 1}]
        })

        assert response.status_code == 401

    def test_create_order_non_customer(self, client, admin_token):
        """Test creating order with admin token returns 403."""
        response = client.post('/orders/', json={
            "order_items": [{"product_id": 1, "quantity": 1}]
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Customer access required"


class TestGetOrders:
    """Test cases for GET /orders/ - Customer and Admin"""

    def test_customer_gets_own_orders(self, app, client, customer_user, sample_products):
        """Test customer can get their own orders with order_items."""
        # Create an order first
        client.post('/orders/', json={
            "order_items": [{"product_id": sample_products[0]["id"], "quantity": 1}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})

        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["user_id"] == customer_user["id"]
        assert "order_items" in data[0]

    def test_customer_only_sees_own_orders(self, app, client, customer_user, admin_user):
        """Test customer sees only their own orders, not other users' orders."""
        with app.app_context():
            own_order = Order(user_id=customer_user["id"], total_amount=100000, status="pending")
            other_order = Order(user_id=admin_user["id"], total_amount=200000, status="pending")
            db.session.add_all([own_order, other_order])
            db.session.commit()

        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["user_id"] == customer_user["id"]

    def test_admin_gets_all_orders(self, app, client, customer_user, admin_user):
        """Test admin can view orders from all customers."""
        with app.app_context():
            order1 = Order(user_id=customer_user["id"], total_amount=100000, status="pending")
            order2 = Order(user_id=admin_user["id"], total_amount=200000, status="pending")
            db.session.add_all([order1, order2])
            db.session.commit()

        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 2

    def test_get_orders_excludes_deleted(self, app, client, customer_user):
        """Test get orders returns only non-deleted orders."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=100000, status="pending", is_deleted=True)
            db.session.add(order)
            db.session.commit()

        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 0

    def test_admin_get_orders_excludes_deleted(self, app, client, customer_user, admin_user):
        """Test admin get orders also excludes soft-deleted orders."""
        with app.app_context():
            active = Order(user_id=customer_user["id"], total_amount=100000, status="pending")
            deleted = Order(user_id=customer_user["id"], total_amount=200000, status="pending", is_deleted=True)
            db.session.add_all([active, deleted])
            db.session.commit()

        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 1

    def test_get_orders_empty(self, client, customer_user):
        """Test customer with no orders gets empty list."""
        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data == []

    def test_get_orders_no_token(self, client):
        """Test getting orders without token returns 401."""
        response = client.get('/orders/')

        assert response.status_code == 401

    def test_get_orders_unknown_role(self, app, client):
        """Test getting orders with an unknown role returns 403."""
        with app.app_context():
            token = create_access_token(identity="99", additional_claims={"role": "guest"})

        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Customer or admin access required"


class TestGetOrderById:
    """Test cases for GET /orders/<id> - Admin only"""

    def test_admin_views_order(self, app, client, admin_token, customer_user):
        """Test admin can view a specific order."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.get(f'/orders/{order_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["order"]["id"] == order_id
        assert data["status"] == "ok"

    def test_get_order_not_found(self, client, admin_token):
        """Test getting non-existent order returns 404."""
        response = client.get('/orders/999',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Order not found"

    def test_get_soft_deleted_order(self, app, client, admin_token, customer_user):
        """Test getting soft-deleted order returns 404."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending", is_deleted=True)
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.get(f'/orders/{order_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Order not found"

    def test_get_order_no_token(self, client):
        """Test getting order without token returns 401."""
        response = client.get('/orders/1')

        assert response.status_code == 401

    def test_get_order_non_admin(self, client, customer_token):
        """Test getting order with customer token returns 403."""
        response = client.get('/orders/1',
            headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"


class TestUpdateOrder:
    """Test cases for PUT /orders/<id> - Admin (any status) and Customer (cancel own pending)"""

    # ==================== Admin Cases ====================

    def test_admin_updates_status_successfully(self, app, client, admin_user, customer_user):
        """Test admin can update order status to any valid value."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "processing"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Order updated successfully"
        assert data["order"]["status"] == "processing"

    def test_admin_full_forward_flow(self, app, client, admin_user, customer_user):
        """Test admin can advance an order through the full valid flow."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        headers = {"Authorization": f"Bearer {admin_user['token']}"}

        for expected in ["processing", "delivering", "completed"]:
            response = client.put(f'/orders/{order_id}', json={"status": expected}, headers=headers)
            data = response.get_json()
            assert response.status_code == 200
            assert data["order"]["status"] == expected

    def test_admin_cannot_revert_status(self, app, client, admin_user, customer_user):
        """Test admin cannot revert status backwards (processing -> pending)."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="processing")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "pending"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "Cannot change status" in data["message"]

    def test_admin_cannot_skip_status(self, app, client, admin_user, customer_user):
        """Test admin cannot skip statuses (pending -> delivering)."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "delivering"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "Cannot change status" in data["message"]

    def test_admin_can_cancel_from_delivering(self, app, client, admin_user, customer_user):
        """Test admin can cancel an order that is in delivering status (Option A)."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="delivering")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "cancelled"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["order"]["status"] == "cancelled"

    def test_admin_cancel_restocks_products(self, app, client, admin_user, customer_user, sample_products):
        """Test cancelling an order restores product stock."""
        # Customer creates an order (reduces stock by 2)
        client.post('/orders/', json={
            "order_items": [{"product_id": sample_products[0]["id"], "quantity": 2}]
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})

        with app.app_context():
            order = Order.query.filter_by(user_id=customer_user["id"]).first()
            order_id = order.id
            product = Product.query.get(sample_products[0]["id"])
            stock_after_order = product.stock

        # Admin cancels the order
        response = client.put(f'/orders/{order_id}', json={
            "status": "cancelled"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})

        assert response.status_code == 200
        with app.app_context():
            product = Product.query.get(sample_products[0]["id"])
            assert product.stock == stock_after_order + 2

    # ==================== Validation Cases ====================

    def test_update_order_missing_status(self, app, client, admin_user, customer_user):
        """Test updating order without status returns 400."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={},
            headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide a status"

    def test_update_order_invalid_status(self, app, client, admin_user, customer_user):
        """Test updating order with an invalid status returns 400."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "flying"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 400
        assert "Invalid status" in data["message"]

    def test_update_order_not_found(self, client, admin_user):
        """Test updating non-existent order returns 404."""
        response = client.put('/orders/999', json={
            "status": "processing"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Order not found"

    def test_update_completed_order(self, app, client, admin_user, customer_user):
        """Test updating an already completed order returns 409."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="completed")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "processing"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "already completed" in data["message"]

    def test_update_cancelled_order(self, app, client, admin_user, customer_user):
        """Test updating an already cancelled order returns 409."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="cancelled")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "processing"
        }, headers={"Authorization": f"Bearer {admin_user['token']}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "already cancelled" in data["message"]

    # ==================== Customer Cases ====================

    def test_customer_cancels_own_pending_order(self, app, client, customer_user):
        """Test customer can cancel their own pending order."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "cancelled"
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["order"]["status"] == "cancelled"

    def test_customer_cannot_update_other_users_order(self, app, client, customer_user, admin_user):
        """Test customer cannot update another user's order."""
        with app.app_context():
            order = Order(user_id=admin_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "cancelled"
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "You can only update your own orders"

    def test_customer_cannot_set_non_cancelled_status(self, app, client, customer_user):
        """Test customer cannot set a status other than cancelled."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "processing"
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Customers can only cancel their orders"

    def test_customer_cannot_cancel_non_pending_order(self, app, client, customer_user):
        """Test customer cannot cancel an order that is not pending."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="processing")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.put(f'/orders/{order_id}', json={
            "status": "cancelled"
        }, headers={"Authorization": f"Bearer {customer_user['token']}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "currently processing" in data["message"]

    # ==================== Auth Cases ====================

    def test_update_order_no_token(self, client):
        """Test updating order without token returns 401."""
        response = client.put('/orders/1', json={"status": "processing"})

        assert response.status_code == 401

    def test_update_order_unknown_role(self, app, client):
        """Test updating order with an unknown role returns 403."""
        with app.app_context():
            token = create_access_token(identity="99", additional_claims={"role": "guest"})

        response = client.put('/orders/1', json={
            "status": "processing"
        }, headers={"Authorization": f"Bearer {token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Customer or admin access required"


class TestDeleteOrder:
    """Test cases for DELETE /orders/<id> - Admin only"""

    def test_admin_deletes_order_successfully(self, app, client, admin_token, customer_user):
        """Test admin can soft-delete an order."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.delete(f'/orders/{order_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Order deleted successfully"

    def test_delete_order_not_found(self, client, admin_token):
        """Test deleting non-existent order returns 404."""
        response = client.delete('/orders/999',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Order not found"

    def test_delete_order_delivering_status(self, app, client, admin_token, customer_user):
        """Test cannot delete order with 'delivering' status."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="delivering")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.delete(f'/orders/{order_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "delivering" in data["message"]

    def test_delete_order_processing_status(self, app, client, admin_token, customer_user):
        """Test cannot delete order with 'processing' status."""
        with app.app_context():
            order = Order(user_id=customer_user["id"], total_amount=199000, status="processing")
            db.session.add(order)
            db.session.commit()
            order_id = order.id

        response = client.delete(f'/orders/{order_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 409
        assert "processing" in data["message"]

    def test_delete_order_no_token(self, client):
        """Test deleting order without token returns 401."""
        response = client.delete('/orders/1')

        assert response.status_code == 401

    def test_delete_order_non_admin(self, client, customer_token):
        """Test deleting order with customer token returns 403."""
        response = client.delete('/orders/1',
            headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"
