# coding: utf-8
from app import db


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    order_id = db.Column(db.ForeignKey('orders.id', ondelete='RESTRICT'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='pending', server_default='pending')
    transaction_id = db.Column(db.String(100), nullable=True, unique=True)
    midtrans_order_id = db.Column(db.String(100), nullable=True, unique=True)
    signature_key = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
    updated_at = db.Column(db.DateTime, nullable=True)

    order = db.relationship('Order', primaryjoin='Payment.order_id == Order.id', backref='payments')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'amount': float(self.amount),
            'method': self.method,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'midtrans_order_id': self.midtrans_order_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
