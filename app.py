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
    # Only browser requests from these origins are permitted. Bearer tokens
    # travel in the Authorization header, so credentials support is not needed.
    frontend_origins = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]
    CORS(
        app,
        resources={r"/*": {"origins": frontend_origins}},
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
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
