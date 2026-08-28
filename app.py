from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)

db = SQLAlchemy(app)
jwt = JWTManager(app)

migrate = Migrate(app, db)

from models import User, Product, Category, Order, order_items

from routes import main_bp, user_bp, auth_bp, product_bp, category_bp, order_bp

app.register_blueprint(main_bp)
app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(product_bp)
app.register_blueprint(category_bp)
app.register_blueprint(order_bp)