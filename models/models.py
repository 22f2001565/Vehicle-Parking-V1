from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime

db= SQLAlchemy()

class User(db.Model):
    __tablename__= 'users'
    id= db.Column(db.Integer, primary_key=True)
    email= db.Column(db.String, unique=True, nullable=False)
    password= db.Column(db.String, nullable=False)
    full_name= db.Column(db.String)
    address= db.Column(db.String)
    pincode= db.Column(db.String)
    type= db.Column(db.String, default="general")

    reservations= relationship('Reservation', back_populates='user')

class ParkingLot(db.Model):
    __tablename__= 'parking_lots'
    id= db.Column(db.Integer, primary_key=True)
    prime_location_name= db.Column(db.String, nullable=False)
    price= db.Column(db.Float, nullable=False)
    address= db.Column(db.String)
    pin_code= db.Column(db.String)
    number_of_spots= db.Column(db.Integer)

    spots= relationship('ParkingSpot', back_populates='lot')

class ParkingSpot(db.Model):
    __tablename__= 'parking_spots'
    id= db.Column(db.Integer, primary_key=True)
    lot_id= db.Column(db.Integer, db.ForeignKey('parking_lots.id'), nullable=False)
    status= db.Column(db.String, default="A")

    lot= relationship('ParkingLot', back_populates='spots')
    reservations= relationship('Reservation', back_populates='spot')

class Reservation(db.Model):
    __tablename__= 'reservations'
    id= db.Column(db.Integer, primary_key=True)
    spot_id= db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=True)
    user_id= db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_num= db.Column(db.String, nullable=False)
    parking_timestamp= db.Column(DateTime)
    leaving_timestamp= db.Column(DateTime)
    parking_cost= db.Column(db.Float)

    user= relationship('User', back_populates='reservations')
    spot= relationship('ParkingSpot', back_populates='reservations')