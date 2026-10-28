import pytest
from unittest.mock import patch
from flask_jwt_extended import decode_token


def _get_cookie(response, name):
    """Return the value of a Set-Cookie named `name`, or None if absent.

    flask-jwt-extended emits several cookies on login:
      - access_token_cookie / refresh_token_cookie  (HttpOnly, the JWTs)
      - csrf_access_token / csrf_refresh_token       (readable, CSRF tokens)
    """
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith(f"{name}="):
            # "name=value; Path=/; HttpOnly; ..." -> value
            return header.split("=", 1)[1].split(";", 1)[0]
    return None


class TestLoginRoute:
    # Test cases for POST /auth/login

    # ==================== Successful Cases ====================

    def test_login_with_valid_credentials(self, client, sample_user):
        # Test successful login returns 200 with user name and sets JWT cookies.
        response = client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Login successful"
        assert data["name"] == sample_user["name"]
        assert data["status"] == "ok"
        # Tokens must NOT be returned in the body anymore.
        assert "access_token" not in data
        assert "refresh_token" not in data
        # Tokens are delivered as cookies instead.
        assert _get_cookie(response, "access_token_cookie") is not None
        assert _get_cookie(response, "refresh_token_cookie") is not None

    def test_login_sets_httponly_jwt_cookies(self, client, sample_user):
        # Test the JWT cookies are flagged HttpOnly (unreadable by JavaScript).
        response = client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })

        set_cookies = response.headers.getlist("Set-Cookie")
        access_cookie = next(c for c in set_cookies if c.startswith("access_token_cookie="))
        refresh_cookie = next(c for c in set_cookies if c.startswith("refresh_token_cookie="))

        assert "HttpOnly" in access_cookie
        assert "HttpOnly" in refresh_cookie

    def test_login_sets_readable_csrf_cookies(self, client, sample_user):
        # Test the CSRF token cookies are set and are NOT HttpOnly, so the
        # front-end can read them and echo them back in the X-CSRF-TOKEN header.
        response = client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })

        set_cookies = response.headers.getlist("Set-Cookie")
        csrf_access = next(c for c in set_cookies if c.startswith("csrf_access_token="))

        assert _get_cookie(response, "csrf_access_token") is not None
        assert "HttpOnly" not in csrf_access

    def test_login_tokens_contain_correct_role_claim(self, app, client, sample_user):
        # Test that the access token cookie contains the correct role claim.
        response = client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })

        access_token = _get_cookie(response, "access_token_cookie")
        assert access_token is not None

        with app.app_context():
            decoded = decode_token(access_token)
            assert decoded["role"] == sample_user["role"]

    # ==================== Failed Cases (400 - Bad Request) ====================

    def test_login_missing_email(self, client, sample_user):
        # Test login with missing email returns 400.
        response = client.post('/auth/login', json={
            "password": "password123"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide email and password"
        assert data["status"] == "error"

    def test_login_missing_password(self, client, sample_user):
        # Test login with missing password returns 400.
        response = client.post('/auth/login', json={
            "email": "test@example.com"
        })
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide email and password"
        assert data["status"] == "error"

    def test_login_missing_both_fields(self, client, sample_user):
        # Test login with empty body returns 400.
        response = client.post('/auth/login', json={})
        data = response.get_json()

        assert response.status_code == 400
        assert data["message"] == "Please provide email and password"
        assert data["status"] == "error"

    # ==================== Failed Cases (401 - Unauthorized) ====================

    def test_login_email_not_found(self, client, sample_user):
        # Test login with non-existent email returns 401.
        response = client.post('/auth/login', json={
            "email": "nonexistent@example.com",
            "password": "password123"
        })
        data = response.get_json()

        assert response.status_code == 401
        assert data["message"] == "Invalid email or password"
        assert data["status"] == "error"

    def test_login_wrong_password(self, client, sample_user):
        # Test login with wrong password returns 401.
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
        # Test login returns 500 when a database error occurs.
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


class TestRefreshRoute:
    # Test cases for POST /auth/refresh

    def _login(self, client, sample_user):
        # Log in so the test client's cookie jar holds the JWT + CSRF cookies.
        return client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })

    def test_refresh_with_valid_cookie(self, client, sample_user):
        # Test refresh issues a new access token cookie when the refresh cookie
        # and matching CSRF header are supplied.
        login_response = self._login(client, sample_user)
        csrf_refresh = _get_cookie(login_response, "csrf_refresh_token")

        # The test client reuses the cookie jar, so the refresh cookie is sent
        # automatically; CSRF protection still requires the header.
        response = client.post('/auth/refresh', headers={"X-CSRF-TOKEN": csrf_refresh})
        data = response.get_json()

        assert response.status_code == 200
        assert data["status"] == "ok"
        assert "access_token" not in data
        assert _get_cookie(response, "access_token_cookie") is not None

    def test_refresh_without_csrf_header_is_rejected(self, client, sample_user):
        # Test refresh is rejected (401) when the CSRF header is missing, even
        # though the refresh cookie is present.
        self._login(client, sample_user)

        response = client.post('/auth/refresh')

        assert response.status_code == 401

    def test_refresh_without_cookie_is_rejected(self, client, sample_user):
        # Test refresh is rejected (401) when no refresh cookie is present.
        response = client.post('/auth/refresh')

        assert response.status_code == 401


class TestLogoutRoute:
    # Test cases for POST /auth/logout

    def test_logout_returns_ok(self, client, sample_user):
        # Test logout succeeds and reports status ok.
        client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })

        response = client.post('/auth/logout')
        data = response.get_json()

        assert response.status_code == 200
        assert data["message"] == "Logout successful"
        assert data["status"] == "ok"

    def test_logout_clears_jwt_cookies(self, client, sample_user):
        # Test logout unsets the JWT cookies (emitted with an empty value).
        client.post('/auth/login', json={
            "email": sample_user["email"],
            "password": sample_user["password"]
        })

        response = client.post('/auth/logout')

        # unset_jwt_cookies re-sends the cookies with an empty value to clear them.
        assert _get_cookie(response, "access_token_cookie") == ""
        assert _get_cookie(response, "refresh_token_cookie") == ""
