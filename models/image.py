# coding: utf-8
from app import db


class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    product_id = db.Column(db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
    is_deleted = db.Column(db.Boolean, nullable=False, server_default=db.text('false'))
    deleted_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship(
        'Product',
        primaryjoin='Image.product_id == Product.id',
        backref=db.backref('images', lazy='dynamic')
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'url': self.url,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
