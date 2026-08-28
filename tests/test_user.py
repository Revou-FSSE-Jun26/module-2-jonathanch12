import pytest
from unittest.mock import patch
from app import db
from models import User


class TestRegisterRoute:
    # Test cases for POST /users/

    # ==================== Successful Cases ====================

    def test_register_with_valid_data(self, client):
        # Test successful registration returns 201 with user data.
        response = client.post('/users/', json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "securepass123",
            "address": "456 New Street"
        })
        data = response.get_json()

        assert response.status_code == 201
        assert data["message"] == "User registration successfull"
        assert data["status"] == "ok"
        assert data["user"]["name"] == "New User"
        assert data["user"]["email"] == "newuser@example.com"
        assert "password" not in data["user"]

    def test_password_is_stored_hashed(self, app, client):
        # Test that the password is stored as a bcrypt hash, not plaintext.
        client.post('/users/', json={
            "name": "Hash Test",
            "email": "hashtest@example.com",
            "password": "plaintext123",
            "address": "789 Hash Ave"
        })

        with app.app_context():
            user = User.query.filter_by(email="hashtest@example.com").first()
            assert user is not None
            assert user.password != "plaintext123"
            assert user.password.startswith("$2b$")

    # ==================== Failed Cases (400 - Missing Fields) ====================

    def test_register_missing_name(self, client):
        # Test registration with missing name returns 400.
        response = client.post('/users/', json={
            "email": "test@example.com",
            "password": "password123",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"
        assert data["status"] == "error"

    def test_register_missing_email(self, client):
        # Test registration with missing email returns 400.
        response = client.post('/users/', json={
            "name": "Test User",
            "password": "password123",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"
        assert data["status"] == "error"

    def test_register_missing_password(self, client):
        # Test registration with missing password returns 400.
        response = client.post('/users/', json={
            "name": "Test User",
            "email": "test@example.com",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"
        assert data["status"] == "error"

    def test_register_missing_address(self, client):
        # Test registration with missing address returns 400.
        response = client.post('/users/', json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"
        assert data["status"] == "error"

    def test_register_empty_body(self, client):
        # Test registration with empty body returns 400.
        response = client.post('/users/', json={})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"
        assert data["status"] == "error"

    # ==================== Failed Cases (400 - Validation Errors) ====================

    def test_register_name_not_string(self, client):
        # Test registration with non-string name returns 400.
        response = client.post('/users/', json={
            "name": 12345,
            "email": "test@example.com",
            "password": "password123",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Name must be a string"

    def test_register_password_too_short(self, client):
        # Test registration with password shorter than 8 characters returns 400.
        response = client.post('/users/', json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "short",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Password must be at least 8 characters"

    # ==================== Failed Cases (409 - Conflict) ====================

    def test_register_duplicate_email(self, client, sample_user):
        # Test registration with existing email returns 409.
        response = client.post('/users/', json={
            "name": "Another User",
            "email": sample_user["email"],
            "password": "password123",
            "address": "999 Duplicate Ave"
        })
        data = response.get_json()

        assert response.status_code == 409
        assert data["message"] == "Please use another email"
        assert data["status"] == "error"

    # ==================== Failed Cases (500 - Server Error) ====================

    def test_register_server_error(self, client):
        # Test registration returns 500 when a database error occurs.
        with patch('routes.user.db.session.add', side_effect=Exception("Database error")):
            response = client.post('/users/', json={
                "name": "Error User",
                "email": "error@example.com",
                "password": "password123",
                "address": "123 Error Street"
            })
            data = response.get_json()

            assert response.status_code == 500
            assert data["message"] == "User registration error"
            assert data["status"] == "error"
