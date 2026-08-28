import pytest
import bcrypt
from flask_jwt_extended import create_access_token
from app import create_app, db
from models import User


@pytest.fixture
def app():
    """Create a test app with an in-memory SQLite database."""
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key',
    }
    app = create_app(config=test_config)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def admin_token(app):
    """Generate a JWT access token with admin role."""
    with app.app_context():
        return create_access_token(identity="1", additional_claims={"role": "admin"})


@pytest.fixture
def customer_token(app):
    """Generate a JWT access token with customer role."""
    with app.app_context():
        return create_access_token(identity="2", additional_claims={"role": "customer"})


@pytest.fixture
def sample_user(app):
    """Create a sample user in the test database."""
    with app.app_context():
        hashed_password = bcrypt.hashpw("password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(
            name="Test User",
            email="test@example.com",
            password=hashed_password,
            address="123 Test Street",
            role="customer"
        )
        db.session.add(user)
        db.session.commit()
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "password": "password123",
            "role": user.role
        }
