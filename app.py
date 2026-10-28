from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from datetime import timedelta
import os
from dotenv import load_dotenv
import cloudinary

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(config=None):
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

    # JWT delivery via HttpOnly cookies instead of the Authorization header.
    # HttpOnly cookies are unreadable by JavaScript, which protects the token
    # against XSS theft. The browser attaches them automatically on requests
    # that opt into sending credentials.
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    # Secure=True restricts cookies to HTTPS. Frontend and backend live on
    # separate origins, so cross-site cookies require SameSite=None, which in
    # turn requires Secure=True. Keep this True in every deployed environment;
    # only set JWT_COOKIE_SECURE=false for plain-HTTP local development.
    app.config['JWT_COOKIE_SECURE'] = os.getenv("JWT_COOKIE_SECURE", "true").lower() == "true"
    app.config['JWT_COOKIE_SAMESITE'] = 'None'
    # Scope the refresh cookie so it is only sent to the refresh endpoint.
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/auth/refresh'
    # CSRF double-submit protection. flask-jwt-extended also sets a readable
    # csrf_access_token / csrf_refresh_token cookie; the frontend must echo it
    # back in the X-CSRF-TOKEN header on state-changing requests.
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True
    app.config['JWT_CSRF_CHECK_FORM'] = False

    # Midtrans payment gateway configuration
    app.config['MIDTRANS_SERVER_KEY'] = os.getenv("MIDTRANS_SERVER_KEY")
    app.config['MIDTRANS_CLIENT_KEY'] = os.getenv("MIDTRANS_CLIENT_KEY")
    app.config['MIDTRANS_IS_PRODUCTION'] = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"

    # Cloudinary media storage configuration
    app.config['CLOUDINARY_CLOUD_NAME'] = os.getenv("CLOUDINARY_CLOUD_NAME")
    app.config['CLOUDINARY_API_KEY'] = os.getenv("CLOUDINARY_API_KEY")
    app.config['CLOUDINARY_API_SECRET'] = os.getenv("CLOUDINARY_API_SECRET")

    # Override with any test/custom config
    if config:
        app.config.update(config)

    # Initialize the Cloudinary SDK from app config
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET'),
        secure=True,
    )

    # Cross-Origin Resource Sharing for the separate front-end app.
    # FRONTEND_ORIGINS is a comma-separated list of allowed origins
    # (e.g. "http://localhost:3000,https://your-frontend.vercel.app").
    # JWTs now travel in HttpOnly cookies, so the browser only sends them on
    # credentialed cross-origin requests. supports_credentials=True is required
    # for that, and it forbids a wildcard origin, so origins must be explicit.
    # X-CSRF-TOKEN is allowed so the front-end can submit the double-submit
    # CSRF token on state-changing requests.
    frontend_origins = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    CORS(
        app,
        resources={r"/*": {"origins": frontend_origins}},
        allow_headers=["Content-Type", "Authorization", "X-CSRF-TOKEN"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        supports_credentials=True,
    )

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    from models import User, Product, Category, Order, order_items, Image, Payment
    from routes import main_bp, user_bp, auth_bp, product_bp, category_bp, order_bp, image_bp, payment_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(payment_bp)

    return app
