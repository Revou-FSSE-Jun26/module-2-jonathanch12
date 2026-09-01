import sys
import os

# Add parent directory to path so we can import app and models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from models import Order, Product, order_items


def seed_orders():
    orders = [
        {"user_id": 4, "total_amount": 998000, "status": "completed"},
        {"user_id": 2, "total_amount": 350000, "status": "processing"},
        {"user_id": 3, "total_amount": 1370000, "status": "completed"},
        {"user_id": 4, "total_amount": 275000, "status": "completed"},
        {"user_id": 5, "total_amount": 850000, "status": "processing"},
    ]

    created = 0
    for order_data in orders:
        order = Order(
            user_id=order_data["user_id"],
            total_amount=order_data["total_amount"],
            status=order_data["status"]
        )
        db.session.add(order)
        created += 1

    db.session.commit()
    print(f"Seeded {created} orders.")


def seed_order_items():
    items = [
        {"order_id": 1, "product_id": 1, "quantity": 1, "unit_price": 199000},
        {"order_id": 1, "product_id": 2, "quantity": 1, "unit_price": 799000},
        {"order_id": 2, "product_id": 3, "quantity": 1, "unit_price": 350000},
        {"order_id": 3, "product_id": 4, "quantity": 2, "unit_price": 450000},
        {"order_id": 3, "product_id": 7, "quantity": 2, "unit_price": 180000},
        {"order_id": 4, "product_id": 8, "quantity": 1, "unit_price": 275000},
        {"order_id": 5, "product_id": 10, "quantity": 1, "unit_price": 850000},
    ]

    created = 0
    for item_data in items:
        # Skip if this order_id/product_id pair already exists (composite primary key)
        existing = db.session.query(order_items).filter(
            order_items.c.order_id == item_data["order_id"],
            order_items.c.product_id == item_data["product_id"]
        ).first()

        if not existing:
            db.session.execute(
                order_items.insert().values(
                    order_id=item_data["order_id"],
                    product_id=item_data["product_id"],
                    quantity=item_data["quantity"],
                    unit_price=item_data["unit_price"]
                )
            )
            created += 1

    db.session.commit()
    print(f"Seeded {created} order items.")


def seed_all():
    print("Starting order seeding...")
    seed_orders()
    seed_order_items()
    print("Order seeding completed!")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_all()
