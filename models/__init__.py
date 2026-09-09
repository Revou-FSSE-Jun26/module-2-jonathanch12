# coding: utf-8
"""Models package.

Re-exports all models and the order_items association table so that
existing imports like `from models import User` continue to work.
"""
from models.category import Category
from models.order import Order, order_items
from models.product import Product
from models.user import User

__all__ = ['Category', 'Order', 'order_items', 'Product', 'User']
