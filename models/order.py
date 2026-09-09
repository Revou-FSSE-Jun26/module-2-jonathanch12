# coding: utf-8
from app import db


order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True, nullable=False),
    db.Column('quantity', db.Integer, nullable=False),
    db.Column('unit_price', db.Numeric(10, 2), nullable=False)
)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    user_id = db.Column(db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending', server_default='pending')
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
    is_deleted = db.Column(db.Boolean, nullable=False, server_default=db.text('false'))
    deleted_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', primaryjoin='Order.user_id == User.id', backref='orders')
    products = db.relationship('Product', secondary=order_items, backref='orders')

    def to_dict(self):
        # Query order_items for this order
        items = db.session.query(order_items).filter(order_items.c.order_id == self.id).all()
        items_list = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price)
            }
            for item in items
        ]

        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'order_items': items_list,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
