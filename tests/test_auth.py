import pytest
from unittest.mock import patch
from flask_jwt_extended import decode_token


class TestLoginRoute:
    """Test cases for POST /auth/login"""

    # ==================== Successful Cases ====================

    def test_login_with_valid_credentials(self, client, sample_user):
        """Test successful login returns 200 with tokens and user name."""
        response = client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Login successful"
        assert data["name"] == sample_user["name"]
        assert data["status"] == "ok"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_tokens_contain_correct_role_claim(self, app, client, sample_user):
        """Test that JWT tokens contain the correct role claim."""
        response = client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })
        data = response.get_json()

        with app.app_context():
            decoded = decode_token(data["access_token"])
            assert decoded["role"] == sample_user["role"]

    # ==================== Failed Cases (400 - Bad Request) ====================

    def test_login_missing_email(self, client, sample_user):
        """Test login with missing email returns 400."""
        response = client.post('/auth/login', json={
            "password": "password123"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide email and password"
        assert data["status"] == "error"

    def test_login_missing_password(self, client, sample_user):
        """Test login with missing password returns 400."""
        response = client.post('/auth/login', json={
            "email": "test@example.com"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide email and password"
        assert data["status"] == "error"

    def test_login_missing_both_fields(self, client, sample_user):
        """Test login with empty body returns 400."""
        response = client.post('/auth/login', json={})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide email and password"
        assert data["status"] == "error"

    # ==================== Failed Cases (401 - Unauthorized) ====================

    def test_login_email_not_found(self, client, sample_user):
        """Test login with non-existent email returns 401."""
        response = client.post('/auth/login', json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        data = response.get_json()

        assert response.status_code == 401
        assert data["message"] == "Invalid email or password"
        assert data["status"] == "error"

    def test_login_wrong_password(self, client, sample_user):
        """Test login with wrong password returns 401."""
        response = client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": "wrongpassword"
        })
        data = response.get_json()

        assert response.status_code == 401
        assert data["message"] == "Invalid email or password"
        assert data["status"] == "error"

    # ==================== Failed Cases (500 - Server Error) ====================

    def test_login_server_error(self, client, sample_user):
        """Test login returns 500 when a database error occurs."""
        with patch('routes.auth.User.query') as mock_query:
            mock_query.filter_by.side_effect = Exception("Database connection failed")

            response = client.post('/auth/login', json={
                "email": "test@example.com",
                "password": "password123"
            })
            data = response.get_json()

            assert response.status_code == 500
            assert data["message"] == "Login error"
            assert data["status"] == "error"
