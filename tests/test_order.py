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
    """Test cases for GET /orders/ - Customer only"""

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

    def test_get_orders_non_customer(self, client, admin_token):
        """Test getting orders with admin token returns 403."""
        response = client.get('/orders/',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Customer access required"


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
