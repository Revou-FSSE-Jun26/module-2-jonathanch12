import pytest
from app import db
from models import Category, Product


class TestCreateCategory:
    """Test cases for POST /categories/ - Admin only"""

    def test_admin_creates_category_successfully(self, client, admin_token):
        """Test admin can create a category."""
        response = client.post('/categories/', json={
            "name": "Electronics",
            "description": "Electronic gadgets"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 201
        assert data["message"] == "Category created successfully"
        assert data["category"]["name"] == "Electronics"
        assert data["status"] == "ok"

    def test_create_category_missing_name(self, client, admin_token):
        """Test creating category without name returns 400."""
        response = client.post('/categories/', json={
            "description": "Some description"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"

    def test_create_category_duplicate_name(self, app, client, admin_token):
        """Test creating category with existing name returns 409."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

        response = client.post('/categories/', json={
            "name": "Electronics",
            "description": "Another description"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 409
        assert data["message"] == "Category name already exists"

    def test_create_category_no_token(self, client):
        """Test creating category without token returns 401."""
        response = client.post('/categories/', json={
            "name": "Electronics"
        })

        assert response.status_code == 401

    def test_create_category_non_admin(self, client, customer_token):
        """Test creating category with customer token returns 403."""
        response = client.post('/categories/', json={
            "name": "Electronics"
        }, headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"


class TestGetCategories:
    """Test cases for GET /categories/ - Public"""

    def test_get_all_categories(self, app, client):
        """Test getting all non-deleted categories."""
        with app.app_context():
            cat1 = Category(name="Electronics", description="Gadgets")
            cat2 = Category(name="Books", description="Reading material")
            cat3 = Category(name="Deleted", description="Should not appear", is_deleted=True)
            db.session.add_all([cat1, cat2, cat3])
            db.session.commit()

        response = client.get('/categories/')
        data = response.get_json()

        assert response.status_code == 200
        assert len(data) == 2
        names = [cat["name"] for cat in data]
        assert "Electronics" in names
        assert "Books" in names
        assert "Deleted" not in names

    def test_get_categories_empty(self, client):
        """Test getting categories when none exist returns empty list."""
        response = client.get('/categories/')
        data = response.get_json()

        assert response.status_code == 200
        assert data == []


class TestGetCategoryById:
    """Test cases for GET /categories/<id> - Public"""

    def test_get_category_with_products(self, app, client):
        """Test getting category by ID includes its products."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(
                category_id=category.id,
                name="Mouse",
                description="Wireless mouse",
                price=199000,
                stock=50
            )
            db.session.add(product)
            db.session.commit()
            cat_id = category.id

        response = client.get(f'/categories/{cat_id}')
        data = response.get_json()

        assert response.status_code == 200
        assert data["name"] == "Electronics"
        assert len(data["products"]) == 1
        assert data["products"][0]["name"] == "Mouse"

    def test_get_category_not_found(self, client):
        """Test getting non-existent category returns 404."""
        response = client.get('/categories/999')
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Category not found"

    def test_get_soft_deleted_category(self, app, client):
        """Test getting soft-deleted category returns 404."""
        with app.app_context():
            category = Category(name="Deleted", description="Gone", is_deleted=True)
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.get(f'/categories/{cat_id}')
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Category not found"


class TestUpdateCategory:
    """Test cases for PUT /categories/<id> - Admin only"""

    def test_admin_updates_category_successfully(self, app, client, admin_token):
        """Test admin can update a category."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.put(f'/categories/{cat_id}', json={
            "name": "Updated Electronics",
            "description": "Updated description"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Category updated successfully"
        assert data["category"]["name"] == "Updated Electronics"

    def test_update_category_not_found(self, client, admin_token):
        """Test updating non-existent category returns 404."""
        response = client.put('/categories/999', json={
            "name": "Updated"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Category not found"

    def test_update_category_duplicate_name(self, app, client, admin_token):
        """Test updating category to existing name returns 409."""
        with app.app_context():
            cat1 = Category(name="Electronics", description="Gadgets")
            cat2 = Category(name="Books", description="Reading")
            db.session.add_all([cat1, cat2])
            db.session.commit()
            cat2_id = cat2.id

        response = client.put(f'/categories/{cat2_id}', json={
            "name": "Electronics"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 409
        assert data["message"] == "Category name already exists"

    def test_update_category_no_token(self, app, client):
        """Test updating category without token returns 401."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.put(f'/categories/{cat_id}', json={
            "name": "Updated"
        })

        assert response.status_code == 401

    def test_update_category_non_admin(self, app, client, customer_token):
        """Test updating category with customer token returns 403."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.put(f'/categories/{cat_id}', json={
            "name": "Updated"
        }, headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"


class TestDeleteCategory:
    """Test cases for DELETE /categories/<id> - Admin only"""

    def test_admin_deletes_category_successfully(self, app, client, admin_token):
        """Test admin can soft-delete a category."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.delete(f'/categories/{cat_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Category deleted successfully"

    def test_delete_category_not_found(self, client, admin_token):
        """Test deleting non-existent category returns 404."""
        response = client.delete('/categories/999',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Category not found"

    def test_delete_category_with_products(self, app, client, admin_token):
        """Test deleting category that has products returns 409."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()

            product = Product(
                category_id=category.id,
                name="Mouse",
                description="Wireless",
                price=199000,
                stock=50
            )
            db.session.add(product)
            db.session.commit()
            cat_id = category.id

        response = client.delete(f'/categories/{cat_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 409
        assert data["message"] == "Cannot delete category with existing products"

    def test_delete_category_no_token(self, app, client):
        """Test deleting category without token returns 401."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.delete(f'/categories/{cat_id}')

        assert response.status_code == 401

    def test_delete_category_non_admin(self, app, client, customer_token):
        """Test deleting category with customer token returns 403."""
        with app.app_context():
            category = Category(name="Electronics", description="Gadgets")
            db.session.add(category)
            db.session.commit()
            cat_id = category.id

        response = client.delete(f'/categories/{cat_id}',
            headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"
