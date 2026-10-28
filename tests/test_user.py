import pytest
from unittest.mock import patch
from flask_jwt_extended import create_access_token
from app import db
from models import User
from tests._helpers import auth


def _auth_header(client, user_id, role="customer"):
    """Authenticate the test client for the given user id via JWT cookie + CSRF.

    JWTs now travel in HttpOnly cookies rather than the Authorization header.
    This mints a token, sets it on the client's cookie jar, and returns the
    X-CSRF-TOKEN header the backend requires on state-changing requests.
    """
    with client.application.app_context():
        token = create_access_token(
            identity=str(user_id),
            additional_claims={"role": role}
        )
        return auth(client, token)


class TestRegisterRoute:
    # Test cases for POST /users/

    # ==================== Successful Cases ====================

    def test_register_with_valid_data(self, client):
        # Test successful registration returns 201 with user data.
        response = client.post('/users/', json={
            "name": "New User",
            "email": "newuser@example.com",
            "phone": "1234567890",
            "password": "securepass123",
            "address": "456 New Street"
        })
        data = response.get_json()

        assert response.status_code == 201
        assert data["message"] == "User registration successfull"
        assert data["status"] == "ok"
        assert data["user"]["name"] == "New User"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["phone"] == "1234567890"
        assert "password" not in data["user"]

    def test_password_is_stored_hashed(self, app, client):
        # Test that the password is stored as a bcrypt hash, not plaintext.
        client.post('/users/', json={
            "name": "Hash Test",
            "email": "hashtest@example.com",
            "phone": "1234567890",
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
            "phone": "1234567890",
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
            "phone": "1234567890",
            "password": "password123",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please fill missing fields"
        assert data["status"] == "error"

    def test_register_missing_phone(self, client):
        # Test registration with missing phone returns 400.
        response = client.post('/users/', json={
            "name": "Test User",
            "email": "test@example.com",
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
            "phone": "1234567890",
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
            "phone": "1234567890",
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
            "phone": "1234567890",
            "password": "password123",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Name must be a string"

    def test_register_phone_not_string(self, client):
        # Test registration with non-string phone returns 400.
        response = client.post('/users/', json={
            "name": "Test User",
            "email": "test@example.com",
            "phone": 1234567890,
            "password": "password123",
            "address": "123 Street"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Phone must be a string"

    def test_register_password_too_short(self, client):
        # Test registration with password shorter than 8 characters returns 400.
        response = client.post('/users/', json={
            "name": "Test User",
            "email": "test@example.com",
            "phone": "1234567890",
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
            "phone": "1234567890",
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
                "phone": "1234567890",
                "password": "password123",
                "address": "123 Error Street"
            })
            data = response.get_json()

            assert response.status_code == 500
            assert data["message"] == "User registration error"
            assert data["status"] == "error"


class TestGetUserDataRoute:
    # Test cases for GET /users/

    # ==================== Successful Cases ====================

    def test_get_user_data_authenticated(self, app, client, sample_user):
        # Test authenticated user retrieves their own data returns 200.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.get('/users/', headers=headers)
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Displaying user's data"
        assert data["status"] == "ok"
        assert data["user"]["id"] == sample_user["id"]
        assert data["user"]["email"] == sample_user["email"]
        assert data["user"]["name"] == sample_user["name"]
        assert "password" not in data["user"]

    # ==================== Failed Cases (401 - Unauthorized) ====================

    def test_get_user_data_missing_token(self, client, sample_user):
        # Test request without a JWT returns 401.
        response = client.get('/users/')

        assert response.status_code == 401

    # ==================== Failed Cases (404 - Not Found) ====================

    def test_get_user_data_user_not_found(self, app, client):
        # Test token for a non-existent user returns 404.
        headers = _auth_header(client, 99999)
        response = client.get('/users/', headers=headers)
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "User not found"
        assert data["status"] == "error"

    # ==================== Failed Cases (500 - Server Error) ====================

    def test_get_user_data_server_error(self, app, client, sample_user):
        # Test retrieval returns 500 when a database error occurs.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        with patch('routes.user.User.query') as mock_query:
            mock_query.get.side_effect = Exception("Database error")

            response = client.get('/users/', headers=headers)
            data = response.get_json()

            assert response.status_code == 500
            assert data["message"] == "User data retrieval error"
            assert data["status"] == "error"


class TestUpdateUserDataRoute:
    # Test cases for PUT /users/

    # ==================== Successful Cases ====================

    def test_update_single_field(self, app, client, sample_user):
        # Test updating a single field returns 200 and persists the change.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "name": "Updated Name"
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "User data updated successfully"
        assert data["status"] == "ok"
        assert data["user"]["name"] == "Updated Name"

        with app.app_context():
            user = User.query.get(sample_user["id"])
            assert user.name == "Updated Name"

    def test_update_multiple_fields(self, app, client, sample_user):
        # Test updating name, phone, and address together returns 200.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "name": "Multi Update",
            "phone": "9876543210",
            "address": "500 Updated Blvd"
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "ok"

        with app.app_context():
            user = User.query.get(sample_user["id"])
            assert user.name == "Multi Update"
            assert user.phone == "9876543210"
            assert user.address == "500 Updated Blvd"

    def test_update_password_is_hashed(self, app, client, sample_user):
        # Test updating the password stores a bcrypt hash, not plaintext.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "password": "newsecurepass123"
        })

        assert response.status_code == 200

        with app.app_context():
            user = User.query.get(sample_user["id"])
            assert user.password != "newsecurepass123"
            assert user.password.startswith("$2b$")

    def test_update_leaves_absent_fields_unchanged(self, app, client, sample_user):
        # Test fields not present in the body are left unchanged.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "name": "Only Name Changed"
        })

        assert response.status_code == 200

        with app.app_context():
            user = User.query.get(sample_user["id"])
            assert user.name == "Only Name Changed"
            assert user.phone == sample_user["phone"]
            assert user.email == sample_user["email"]

    # ==================== Failed Cases (400 - Bad Request) ====================

    def test_update_empty_body(self, app, client, sample_user):
        # Test update with empty body returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide fields to update"
        assert data["status"] == "error"

    def test_update_disallowed_field_email(self, app, client, sample_user):
        # Test updating a disallowed field (email) returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "email": "newemail@example.com"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert "email" in data["error"]
        assert data["status"] == "error"

    def test_update_disallowed_field_role(self, app, client, sample_user):
        # Test updating a disallowed field (role) returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "role": "admin"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert "role" in data["error"]

    def test_update_name_not_string(self, app, client, sample_user):
        # Test update with non-string name returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "name": 12345
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Name must be a string"

    def test_update_name_empty(self, app, client, sample_user):
        # Test update with whitespace-only name returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "name": "   "
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Name must not be empty"

    def test_update_phone_not_string(self, app, client, sample_user):
        # Test update with non-string phone returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "phone": 1234567890
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Phone must be a string"

    def test_update_phone_empty(self, app, client, sample_user):
        # Test update with empty phone returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "phone": ""
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Phone must not be empty"

    def test_update_address_empty(self, app, client, sample_user):
        # Test update with whitespace-only address returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "address": "  "
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Address must not be empty"

    def test_update_password_empty(self, app, client, sample_user):
        # Test update with whitespace-only password returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "password": "        "
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Password must not be empty"

    def test_update_password_too_short(self, app, client, sample_user):
        # Test update with password shorter than 8 characters returns 400.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        response = client.put('/users/', headers=headers, json={
            "password": "short"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Validation error"
        assert data["error"] == "Password must be at least 8 characters"

    # ==================== Failed Cases (401 - Unauthorized) ====================

    def test_update_missing_token(self, client, sample_user):
        # Test update without a JWT returns 401.
        response = client.put('/users/', json={"name": "No Auth"})

        assert response.status_code == 401

    # ==================== Failed Cases (404 - Not Found) ====================

    def test_update_user_not_found(self, app, client):
        # Test token for a non-existent user returns 404.
        headers = _auth_header(client, 99999)
        response = client.put('/users/', headers=headers, json={
            "name": "Ghost User"
        })
        data = response.get_json()

        assert response.status_code == 404
        assert data["message"] == "User not found"
        assert data["status"] == "error"

    # ==================== Failed Cases (500 - Server Error) ====================

    def test_update_server_error(self, app, client, sample_user):
        # Test update returns 500 when a database error occurs.
        headers = _auth_header(client, sample_user["id"], sample_user["role"])
        with patch('routes.user.db.session.commit', side_effect=Exception("Database error")):
            response = client.put('/users/', headers=headers, json={
                "name": "Will Fail"
            })
            data = response.get_json()

            assert response.status_code == 500
            assert data["message"] == "User data update error"
            assert data["status"] == "error"
