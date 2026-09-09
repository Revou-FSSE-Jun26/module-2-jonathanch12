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
