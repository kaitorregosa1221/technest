from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100))
    brand = db.Column(db.String(50))
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)
    description = db.Column(db.Text)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    customer_name = db.Column(db.String(100))
    product_id = db.Column(db.String(50))
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    total_amount = db.Column(db.Float)
    payment_status = db.Column(db.String(50), default='Pending') # The missing piece
    status = db.Column(db.String(50))
    message = db.Column(db.String(255))

class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    action = db.Column(db.String(50))
    details = db.Column(db.Text)