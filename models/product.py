# coding: utf-8
from app import db


class Product(db.Model):
    __tablename__ = 'products'

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
