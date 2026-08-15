# coding: utf-8
from app import db



class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)



class OrderItem(db.Model):
    __tablename__ = 'order_items'

    order_id = db.Column(db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    product_id = db.Column(db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

    order = db.relationship('Order', primaryjoin='OrderItem.order_id == Order.id', backref='order_items')
    product = db.relationship('Product', primaryjoin='OrderItem.product_id == Product.id', backref='order_items')



class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.CheckConstraint("status::text = ANY (ARRAY['pending'::character varying, 'processing'::character varying, 'delivering'::character varying, 'completed'::character varying, 'cancelled'::character varying]::text[])"),
    )

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    user_id = db.Column(db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())

    user = db.relationship('User', primaryjoin='Order.user_id == User.id', backref='orders')



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

    category = db.relationship('Category', primaryjoin='Product.category_id == Category.id', backref='products')



class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
