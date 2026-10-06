import pytest
from app import db
from models import Category, Product, Image


@pytest.fixture
def sample_product(app):
    """Create a category and a product, returning the product id."""
    with app.app_context():
        category = Category(name="Electronics", description="Gadgets")
        db.session.add(category)
        db.session.commit()

        product = Product(category_id=category.id, name="Mouse",
                          description="Wireless", price=199000, stock=50)
        db.session.add(product)
        db.session.commit()
        return product.id


@pytest.fixture
def deleted_product(app):
    """Create a soft-deleted product, returning its id."""
    with app.app_context():
        category = Category(name="Books", description="Reading")
        db.session.add(category)
        db.session.commit()

        product = Product(category_id=category.id, name="Gone",
                          description="Removed", price=100000, stock=10, is_deleted=True)
        db.session.add(product)
        db.session.commit()
        return product.id


def _add_image(app, product_id, url="img", is_deleted=False):
    """Helper to insert an image row directly and return its id."""
    with app.app_context():
        image = Image(product_id=product_id, url=url, is_deleted=is_deleted)
        db.session.add(image)
        db.session.commit()
        return image.id


# =====================================================================
# GET /products/<product_id>/images/ — Public (no auth required)
# =====================================================================
class TestGetProductImages:
    """Test cases for GET /products/<product_id>/images/ - Public"""

    def test_get_images_for_product(self, app, client, sample_product):
        """Test getting all non-deleted images for a product."""
        _add_image(app, sample_product, url="img1")
        _add_image(app, sample_product, url="img2")

        response = client.get(f'/products/{sample_product}/images/')
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "ok"
        assert len(data["images"]) == 2
        urls = [img["url"] for img in data["images"]]
        assert "img1" in urls
        assert "img2" in urls

    def test_get_images_excludes_soft_deleted(self, app, client, sample_product):
        """Test soft-deleted images are not returned."""
        _add_image(app, sample_product, url="active")
        _add_image(app, sample_product, url="deleted", is_deleted=True)

        response = client.get(f'/products/{sample_product}/images/')
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["images"]) == 1
        assert data["images"][0]["url"] == "active"

    def test_get_images_empty(self, client, sample_product):
        """Test a product with no images returns an empty list."""
        response = client.get(f'/products/{sample_product}/images/')
        data = response.get_json()

        assert response.status_code == 200
        assert data["images"] == []

    def test_get_images_product_not_found(self, client):
        """Test getting images for a non-existent product returns 404."""
        response = client.get('/products/999/images/')
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_get_images_soft_deleted_product(self, client, deleted_product):
        """Test getting images for a soft-deleted product returns 404."""
        response = client.get(f'/products/{deleted_product}/images/')
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_customer_can_view_images(self, app, client, customer_token, sample_product):
        """Test a customer (logged-in non-admin) can view images."""
        _add_image(app, sample_product, url="img")

        response = client.get(f'/products/{sample_product}/images/',
            headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["images"]) == 1

    def test_anonymous_can_view_images(self, app, client, sample_product):
        """Test an unauthenticated user can view images (no token)."""
        _add_image(app, sample_product, url="img")

        response = client.get(f'/products/{sample_product}/images/')
        data = response.get_json()

        assert response.status_code == 200
        assert len(data["images"]) == 1


# =====================================================================
# POST /products/<product_id>/images/ — Admin only
# =====================================================================
class TestAddProductImages:
    """Test cases for POST /products/<product_id>/images/ - Admin only"""

    def test_admin_adds_single_image(self, client, admin_token, sample_product):
        """Test admin can add a single image via a JSON object."""
        response = client.post(f'/products/{sample_product}/images/', json={
            "url": "img"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 201
        assert data["status"] == "ok"
        assert len(data["images"]) == 1
        assert data["images"][0]["url"] == "img"
        assert data["images"][0]["product_id"] == sample_product

    def test_admin_adds_multiple_images(self, client, admin_token, sample_product):
        """Test admin can add multiple images via a JSON list."""
        response = client.post(f'/products/{sample_product}/images/', json=[
            {"url": "img1"},
            {"url": "img2"},
            {"url": "img3"}
        ], headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 201
        assert len(data["images"]) == 3
        urls = [img["url"] for img in data["images"]]
        assert urls == ["img1", "img2", "img3"]

    def test_add_image_strips_whitespace(self, client, admin_token, sample_product):
        """Test the url value is trimmed before saving."""
        response = client.post(f'/products/{sample_product}/images/', json={
            "url": "  spaced  "
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 201
        assert data["images"][0]["url"] == "spaced"

    def test_add_image_product_not_found(self, client, admin_token):
        """Test adding an image to a non-existent product returns 404."""
        response = client.post('/products/999/images/', json={
            "url": "img"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_add_image_soft_deleted_product(self, client, admin_token, deleted_product):
        """Test adding an image to a soft-deleted product returns 404."""
        response = client.post(f'/products/{deleted_product}/images/', json={
            "url": "img"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_add_image_empty_list(self, client, admin_token, sample_product):
        """Test posting an empty list returns 400."""
        response = client.post(f'/products/{sample_product}/images/', json=[],
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "No images provided"

    def test_add_image_missing_url(self, client, admin_token, sample_product):
        """Test an image object without a url returns 400."""
        response = client.post(f'/products/{sample_product}/images/', json={
            "caption": "no url here"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert "url" in data["message"]

    def test_add_image_empty_url(self, client, admin_token, sample_product):
        """Test a blank url string returns 400."""
        response = client.post(f'/products/{sample_product}/images/', json={
            "url": "   "
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert "url" in data["message"]

    def test_add_image_url_not_string(self, client, admin_token, sample_product):
        """Test a non-string url returns 400."""
        response = client.post(f'/products/{sample_product}/images/', json={
            "url": 12345
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert "url" in data["message"]

    def test_add_image_rolls_back_on_invalid_item(self, app, client, admin_token, sample_product):
        """Test that a bad item in the list prevents all images from being saved."""
        response = client.post(f'/products/{sample_product}/images/', json=[
            {"url": "good"},
            {"url": ""}
        ], headers={"Authorization": f"Bearer {admin_token}"})

        assert response.status_code == 400
        # No images should have been persisted since the batch failed validation
        with app.app_context():
            count = Image.query.filter_by(product_id=sample_product).count()
            assert count == 0

    def test_add_image_no_token(self, client, sample_product):
        """Test adding an image without a token returns 401."""
        response = client.post(f'/products/{sample_product}/images/', json={
            "url": "img"
        })

        assert response.status_code == 401

    def test_add_image_non_admin(self, client, customer_token, sample_product):
        """Test adding an image with a customer token returns 403."""
        response = client.post(f'/products/{sample_product}/images/', json={
            "url": "img"
        }, headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"


# =====================================================================
# PUT /products/<product_id>/images/<image_id> — Admin only
# =====================================================================
class TestUpdateProductImage:
    """Test cases for PUT /products/<product_id>/images/<image_id> - Admin only"""

    def test_admin_updates_image(self, app, client, admin_token, sample_product):
        """Test admin can update an image's url."""
        image_id = _add_image(app, sample_product, url="old")

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": "new"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Image updated successfully"
        assert data["image"]["url"] == "new"

    def test_update_image_strips_whitespace(self, app, client, admin_token, sample_product):
        """Test the updated url is trimmed."""
        image_id = _add_image(app, sample_product, url="old")

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": "  trimmed  "
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["image"]["url"] == "trimmed"

    def test_update_image_product_not_found(self, client, admin_token):
        """Test updating an image under a non-existent product returns 404."""
        response = client.put('/products/999/images/1', json={
            "url": "new"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_update_image_soft_deleted_product(self, app, client, admin_token, deleted_product):
        """Test updating an image under a soft-deleted product returns 404."""
        image_id = _add_image(app, deleted_product, url="old")

        response = client.put(f'/products/{deleted_product}/images/{image_id}', json={
            "url": "new"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_update_image_not_found(self, client, admin_token, sample_product):
        """Test updating a non-existent image returns 404."""
        response = client.put(f'/products/{sample_product}/images/999', json={
            "url": "new"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Image not found"

    def test_update_soft_deleted_image(self, app, client, admin_token, sample_product):
        """Test updating a soft-deleted image returns 404."""
        image_id = _add_image(app, sample_product, url="gone", is_deleted=True)

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": "new"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Image not found"

    def test_update_image_belongs_to_other_product(self, app, client, admin_token, sample_product):
        """Test updating an image that belongs to another product returns 404."""
        with app.app_context():
            cat = Category.query.first()
            other = Product(category_id=cat.id, name="Other", description="x", price=1000, stock=1)
            db.session.add(other)
            db.session.commit()
            other_id = other.id
        image_id = _add_image(app, other_id, url="belongs-to-other")

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": "new"
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Image not found"

    def test_update_image_empty_url(self, app, client, admin_token, sample_product):
        """Test updating with a blank url returns 400."""
        image_id = _add_image(app, sample_product, url="old")

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": "   "
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert "url" in data["message"]

    def test_update_image_url_not_string(self, app, client, admin_token, sample_product):
        """Test updating with a non-string url returns 400."""
        image_id = _add_image(app, sample_product, url="old")

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": 12345
        }, headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 400
        assert "url" in data["message"]

    def test_update_image_no_token(self, app, client, sample_product):
        """Test updating an image without a token returns 401."""
        image_id = _add_image(app, sample_product, url="old")

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": "new"
        })

        assert response.status_code == 401

    def test_update_image_non_admin(self, app, client, customer_token, sample_product):
        """Test updating an image with a customer token returns 403."""
        image_id = _add_image(app, sample_product, url="old")

        response = client.put(f'/products/{sample_product}/images/{image_id}', json={
            "url": "new"
        }, headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"


# =====================================================================
# DELETE /products/<product_id>/images/<image_id> — Admin only
# =====================================================================
class TestDeleteProductImage:
    """Test cases for DELETE /products/<product_id>/images/<image_id> - Admin only"""

    def test_admin_deletes_image(self, app, client, admin_token, sample_product):
        """Test admin can soft-delete an image."""
        image_id = _add_image(app, sample_product, url="img")

        response = client.delete(f'/products/{sample_product}/images/{image_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Image deleted successfully"

        # Confirm it is soft-deleted, not hard-deleted
        with app.app_context():
            image = Image.query.get(image_id)
            assert image is not None
            assert image.is_deleted is True
            assert image.deleted_at is not None

    def test_deleted_image_excluded_from_listing(self, app, client, admin_token, sample_product):
        """Test a deleted image no longer appears in the GET listing."""
        image_id = _add_image(app, sample_product, url="img")
        client.delete(f'/products/{sample_product}/images/{image_id}',
            headers={"Authorization": f"Bearer {admin_token}"})

        response = client.get(f'/products/{sample_product}/images/')
        data = response.get_json()

        assert response.status_code == 200
        assert data["images"] == []

    def test_delete_image_product_not_found(self, client, admin_token):
        """Test deleting an image under a non-existent product returns 404."""
        response = client.delete('/products/999/images/1',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_delete_image_soft_deleted_product(self, app, client, admin_token, deleted_product):
        """Test deleting an image under a soft-deleted product returns 404."""
        image_id = _add_image(app, deleted_product, url="img")

        response = client.delete(f'/products/{deleted_product}/images/{image_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Product not found"

    def test_delete_image_not_found(self, client, admin_token, sample_product):
        """Test deleting a non-existent image returns 404."""
        response = client.delete(f'/products/{sample_product}/images/999',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Image not found"

    def test_delete_already_deleted_image(self, app, client, admin_token, sample_product):
        """Test deleting an already soft-deleted image returns 404."""
        image_id = _add_image(app, sample_product, url="gone", is_deleted=True)

        response = client.delete(f'/products/{sample_product}/images/{image_id}',
            headers={"Authorization": f"Bearer {admin_token}"})
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "Image not found"

    def test_delete_image_no_token(self, app, client, sample_product):
        """Test deleting an image without a token returns 401."""
        image_id = _add_image(app, sample_product, url="img")

        response = client.delete(f'/products/{sample_product}/images/{image_id}')

        assert response.status_code == 401

    def test_delete_image_non_admin(self, app, client, customer_token, sample_product):
        """Test deleting an image with a customer token returns 403."""
        image_id = _add_image(app, sample_product, url="img")

        response = client.delete(f'/products/{sample_product}/images/{image_id}',
            headers={"Authorization": f"Bearer {customer_token}"})
        data = response.get_json()

        assert response.status_code == 403
        assert data["message"] == "Admin access required"
