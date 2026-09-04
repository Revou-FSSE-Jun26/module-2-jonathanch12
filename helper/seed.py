import sys
import os

# Add parent directory to path so we can import app and models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models import User, Category, Product
import bcrypt


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_users():
    users = [
        {"name": "John Alexander", "email": "john@email.com", "password": "John1234", "address": "Park Ave 123", "role": "admin", "phone": "081234567899"},
        {"name": "Sarah Tan", "email": "sarah@email.com", "password": "Sarah1234", "address": "Milton 1", "role": "customer", "phone": "081345678912"},
        {"name": "Michael Max", "email": "michael@email.com", "password": "Michael1234", "address": "Sora Area", "role": "customer", "phone": "081456789123"},
        {"name": "Alonso Wirtz", "email": "alonso@email.com", "password": "Alonso1234", "address": "Keynes 123", "role": "customer", "phone": "081567891234"},
        {"name": "David Alten", "email": "david@email.com", "password": "David1234", "address": "Stamford 4", "role": "customer", "phone": "081678912345"},
    ]

    for user_data in users:
        existing = User.query.filter_by(email=user_data["email"]).first()
        if not existing:
            user = User(
                name=user_data["name"],
                email=user_data["email"],
                password=hash_password(user_data["password"]),
                address=user_data["address"],
                role=user_data["role"],
                phone=user_data["phone"]
            )
            db.session.add(user)

    db.session.commit()
    print(f"Seeded {len(users)} users.")


def seed_categories():
    categories = [
        {"name": "Electronics", "description": "Electronic gadgets"},
        {"name": "Books", "description": "Educational and fiction books"},
        {"name": "Home", "description": "Home appliances"},
        {"name": "Sports", "description": "Sporting equipment"},
        {"name": "Fashion", "description": "Clothing and accessories"},
    ]

    for cat_data in categories:
        existing = Category.query.filter_by(name=cat_data["name"]).first()
        if not existing:
            category = Category(
                name=cat_data["name"],
                description=cat_data["description"]
            )
            db.session.add(category)

    db.session.commit()
    print(f"Seeded {len(categories)} categories.")


def seed_products():
    products = [
        {"category_id": 1, "name": "Logitech Wireless Mouse", "description": "Bluetooth Mouse", "price": 199000, "stock": 5000},
        {"category_id": 1, "name": "Razer Mechanical Keyboard", "description": "RGB Keyboard", "price": 799000, "stock": 2500},
        {"category_id": 2, "name": "Learning PostgreSQL", "description": "Database Book", "price": 350000, "stock": 4000},
        {"category_id": 2, "name": "Refactoring: Clean Code", "description": "Programming Book", "price": 450000, "stock": 3000},
        {"category_id": 3, "name": "Rice Cooker", "description": "1.8 Liter Rice Cooker", "price": 650000, "stock": 1500},
        {"category_id": 3, "name": "Electric Kettle", "description": "1.5 Liter", "price": 250000, "stock": 3500},
        {"category_id": 4, "name": "Spain RFEF Men Jersey", "description": "Official Size M", "price": 180000, "stock": 6000},
        {"category_id": 4, "name": "Jabulani Ball", "description": "Football Equipment", "price": 275000, "stock": 4500},
        {"category_id": 5, "name": "Hoodie", "description": "Cotton Hoodie", "price": 320000, "stock": 2000},
        {"category_id": 5, "name": "Sneakers", "description": "Running Shoes", "price": 850000, "stock": 1800},
    ]

    for prod_data in products:
        existing = Product.query.filter_by(name=prod_data["name"]).first()
        if not existing:
            product = Product(
                category_id=prod_data["category_id"],
                name=prod_data["name"],
                description=prod_data["description"],
                price=prod_data["price"],
                stock=prod_data["stock"]
            )
            db.session.add(product)

    db.session.commit()
    print(f"Seeded {len(products)} products.")


def seed_all():
    print("Starting database seeding...")
    seed_users()
    seed_categories()
    seed_products()
    print("Database seeding completed!")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_all()
