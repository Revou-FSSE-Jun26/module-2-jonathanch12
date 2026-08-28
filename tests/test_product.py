import pytest
from app import db
from models import Category, Product, Order, order_items


class TestGetProducts:
    """Test cases for GET /products/ - Public"""

    def test_get_all_products(self, app, client):
        """Test getting all non-deleted products."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            p1 = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            p2 = Product(category_id=category.id, name="Keyboard", description="RGB", price=799000, stock=25)
            p3 = Product(category_id=category.id, name="Deleted", description="Gone", price=100000, stock=10, is_deleted=True)
            db.session.add_all([p1, p2, p3])
            db.session.commit()

        response = client.get('/products/')
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 2
        names = [p["name"] for p in data]
        assert "Mouse" in names
        assert "Keyboard" in names
        assert "Deleted" not in names

    def test_get_products_empty(self, client):
        """Test getting products when none exist returns empty list."""
        response = client.get('/products/')
        data = response.get_json()

        assert response.status_code == 200
        assert data == []


class TestGetProductById:
    """Test cases for GET /products/<id> - Public"""

    def test_get_existing_product(self, app, client):
        """Test getting product by ID."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.get(f'/products/{prod_id}')
        data = response.get_json()

        assert response.status_code == 200
        assert data["name"] == "Mouse"

    def test_get_product_not_found(self, client):
        """Test getting non-existent product returns 404."""
        response = client.get('/products/999')
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_get_soft_deleted_product(self, app, client):
        """Test getting soft-deleted product returns 404."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Deleted", description="Gone", price=100000, stock=10, is_deleted=True)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.get(f'/products/{prod_id}')
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"


class TestCreateProduct:
    """Test cases for POST /products/ - Admin only"""

    def test_admin_creates_product_successfully(self, app, client, admin_token):
        """Test admin can create a product."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.post('/products/', json={
            "category_id": cat_id,
            "name": "Mouse",
            "description": "Wireless mouse",
            "price": 199000,
            "stock": 50
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 201
        assert data["message"] == "Product created successfully"
        assert data["product"]["name"] == "Mouse"
        assert data["status"] == "ok"

    def test_create_product_missing_fields(self, client, admin_token):
        """Test creating product with missing fields returns 400."""
        response = client.post('/products/', json={
            "name": "Mouse",
            "price": 199000
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"

    def test_create_product_name_not_string(self, app, client, admin_token):
        """Test creating product with non-string name returns 400."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.post('/products/', json={
            "category_id": cat_id,
            "name": 12345,
            "description": "Invalid name",
            "price": 199000,
            "stock": 50
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["error"] == "Name must be a string"

    def test_create_product_price_not_number(self, app, client, admin_token):
        """Test creating product with non-numeric price returns 400."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.post('/products/', json={
            "category_id": cat_id,
            "name": "Mouse",
            "description": "Wireless",
            "price": "not_a_number",
            "stock": 50
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["error"] == "Price must be a number"

    def test_create_product_price_zero_or_negative(self, app, client, admin_token):
        """Test creating product with price <= 0 returns 400."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.post('/products/', json={
            "category_id": cat_id,
            "name": "Mouse",
            "description": "Wireless",
            "price": 0,
            "stock": 50
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["error"] == "Price must be more than 0"

    def test_create_product_stock_not_integer(self, app, client, admin_token):
        """Test creating product with non-integer stock returns 400."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.post('/products/', json={
            "category_id": cat_id,
            "name": "Mouse",
            "description": "Wireless",
            "price": 199000,
            "stock": 50.5
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["error"] == "Stock must be an integer"

    def test_create_product_stock_negative(self, app, client, admin_token):
        """Test creating product with negative stock returns 400."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.post('/products/', json={
            "category_id": cat_id,
            "name": "Mouse",
            "description": "Wireless",
            "price": 199000,
            "stock": -5
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["error"] == "Stock must be 0 or more"

    def test_create_product_category_not_found(self, client, admin_token):
        """Test creating product with non-existent category returns 404."""
        response = client.post('/products/', json={
            "category_id": 999,
            "name": "Mouse",
            "description": "Wireless",
            "price": 199000,
            "stock": 50
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Category not found"

    def test_create_product_no_token(self, client):
        """Test creating product without token returns 401."""
        response = client.post('/products/', json={
            "category_id": 1,
            "name": "Mouse",
            "description": "Wireless",
            "price": 199000,
            "stock": 50
        })

        assert response.status_code == 401

    def test_create_product_non_admin(self, client, customer_token):
        """Test creating product with customer token returns 403."""
        response = client.post('/products/', json={
            "category_id": 1,
            "name": "Mouse",
            "description": "Wireless",
            "price": 199000,
            "stock": 50
        }, headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"


class TestUpdateProduct:
    """Test cases for PUT /products/<id> - Admin only"""

    def test_admin_updates_product_successfully(self, app, client, admin_token):
        """Test admin can update a product."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.put(f'/products/{prod_id}', json={
            "name": "Updated Mouse",
            "price": 250000
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Product updated successfully"
        assert data["product"]["name"] == "Updated Mouse"

    def test_update_product_not_found(self, client, admin_token):
        """Test updating non-existent product returns 404."""
        response = client.put('/products/999', json={
            "name": "Updated"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_update_product_invalid_category(self, app, client, admin_token):
        """Test updating product with non-existent category returns 404."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.put(f'/products/{prod_id}', json={
            "category_id": 999
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Category not found"

    def test_update_product_no_token(self, app, client):
        """Test updating product without token returns 401."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.put(f'/products/{prod_id}', json={
            "name": "Updated"
        })

        assert response.status_code == 401

    def test_update_product_non_admin(self, app, client, customer_token):
        """Test updating product with customer token returns 403."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.put(f'/products/{prod_id}', json={
            "name": "Updated"
        }, headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"


class TestDeleteProduct:
    """Test cases for DELETE /products/<id> - Admin only"""

    def test_admin_deletes_product_successfully(self, app, client, admin_token):
        """Test admin can soft-delete a product."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.delete(f'/products/{prod_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Product deleted successfully"

    def test_delete_product_not_found(self, client, admin_token):
        """Test deleting non-existent product returns 404."""
        response = client.delete('/products/999',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_delete_product_with_active_orders(self, app, client, admin_token):
        """Test deleting product with active orders returns 409."""
        with app.app_context():
            from models import User
            user = User(name="Test", email="test@test.com", password="hashed", address="123 St", role="customer")
            db.session.add(user)
            db.session.commit()

            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()

            order = Order(user_id=user.id, total_amount=199000, status="pending")
            db.session.add(order)
            db.session.commit()

            db.session.execute(order_items.insert().values(
                order_id=order.id,
                product_id=product.id,
                quantity=1,
                unit_price=199000
            ))
            db.session.commit()
            prod_id = product.id

        response = client.delete(f'/products/{prod_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 409
        assert data["message"] == "Cannot delete product with active orders"

    def test_delete_product_no_token(self, app, client):
        """Test deleting product without token returns 401."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.delete(f'/products/{prod_id}')

        assert response.status_code == 401

    def test_delete_product_non_admin(self, app, client, customer_token):
        """Test deleting product with customer token returns 403."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(category_id=category.id, name="Mouse", description="Wireless", price=199000, stock=50)
            db.session.add(product)
            db.session.commit()
            prod_id = product.id

        response = client.delete(f'/products/{prod_id}',
            headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"
