from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)

from models import User, Product, Category, Order, order_items

from routes import main_bp, user_bp, product_bp

app.register_blueprint(main_bp)
app.register_blueprint(user_bp)
app.register_blueprint(product_bp)