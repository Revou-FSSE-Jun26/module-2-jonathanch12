# coding: utf-8
from app import db



class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, nullable=False, server_default=db.text('false'))
    deleted_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }



order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    db.Column('product_id', db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True, nullable=False),
    db.Column('quantity', db.Integer, nullable=False),
    db.Column('unit_price', db.Numeric(10, 2), nullable=False)
)



class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.CheckConstraint("status::text = ANY (ARRAY['pending'::character varying, 'processing'::character varying, 'delivering'::character varying, 'completed'::character varying, 'cancelled'::character varying]::text[])"),
    )

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    user_id = db.Column(db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, server_default='pending')
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
    is_deleted = db.Column(db.Boolean, nullable=False, server_default=db.text('false'))
    deleted_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', primaryjoin='Order.user_id == User.id', backref='orders')
    products = db.relationship('Product', secondary=order_items, backref='orders')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (
        db.CheckConstraint('price >= 0::numeric'),
        db.CheckConstraint('stock >= 0')
    )

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    category_id = db.Column(db.ForeignKey('categories.id', ondelete='RESTRICT'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
    is_deleted = db.Column(db.Boolean, nullable=False, server_default=db.text('false'))
    deleted_at = db.Column(db.DateTime, nullable=True)

    category = db.relationship('Category', primaryjoin='Product.category_id == Category.id', backref='products')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }



class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
    role = db.Column(db.String(50), nullable=False, server_default='user')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
