from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class ParkingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    car_plate = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    vehicle_type_id = db.Column(db.Integer, db.ForeignKey('vehicle_types.id'), nullable=False)
    slot = db.Column(db.String(20))
    fee = db.Column(db.Float)
    image_path = db.Column(db.String(256))
    user = db.relationship('User', backref='sessions')
    vehicle_type = db.relationship('VehicleType')

class VehicleType(db.Model):
    __tablename__ = 'vehicle_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    rate_per_hour = db.Column(db.Float, nullable=False)
