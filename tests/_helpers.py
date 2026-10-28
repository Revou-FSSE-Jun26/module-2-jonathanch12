"""Shared test helpers for cookie-based JWT authentication.

JWTs now live in HttpOnly cookies instead of the Authorization header, and CSRF
double-submit protection is enabled. The ``auth`` helper lets existing tests
switch from Bearer headers to the cookie + CSRF-header model with a one-line
change at each call site.
"""

from flask_jwt_extended import decode_token

# Cookie name flask-jwt-extended uses for the access token.
ACCESS_COOKIE_NAME = "access_token_cookie"


def auth(client, token):
    """Authenticate a test request using cookie-based JWT + CSRF.

    Mirrors how a browser behaves:

      - Sets the access token on the test client's cookie jar so it is sent on
        subsequent requests (the browser does this automatically for cookies).
      - Returns the X-CSRF-TOKEN header the backend requires on state-changing
        requests. The expected value is embedded in the token as its ``csrf``
        claim, so we decode it rather than guessing.

    Returned as a headers dict so existing call sites can swap
    ``headers={"Authorization": f"Bearer {token}"}`` for
    ``headers=auth(client, token)`` with no other change. GET requests simply
    ignore the unused CSRF header, so the same helper works for every method.
    """
    client.set_cookie(ACCESS_COOKIE_NAME, token)
    csrf = decode_token(token)["csrf"]
    return {"X-CSRF-TOKEN": csrf}
