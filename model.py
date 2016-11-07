"""Modes and database functions for Rideshare Project"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy_utils import ArrowType
import arrow

db = SQLAlchemy()

##############################################################################
# Database Models

class User(db.Model):
    """User of the site. Can be driver (as of now)"""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    photo = db.Column(db.String(300), nullable=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    member_since = db.Column(db.DateTime, default=datetime.now())
    image = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s, name = %s, email=%s, password=%s>" % (self.user_id, 
                                            self.first_name, self.email, self.password)

class Ride(db.Model):
    """A specific ride"""

    __tablename__ = "rides"

    ride_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    driver = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric, nullable=False) #look into this datatype

    # Start Location
    start_lat = db.Column(db.Float(24), nullable=False)
    start_lng = db.Column(db.Float(24), nullable=False)
    start_name = db.Column(db.String(200), nullable=True)
    start_number = db.Column(db.String(50), nullable=True)
    start_street = db.Column(db.String(100), nullable=True)
    start_city = db.Column(db.String(50), nullable=False)
    start_state = db.Column(db.String(15), nullable=False) #add validation
    start_zip = db.Column(db.Integer, nullable=False)
    # End Location
    end_lat = db.Column(db.Float(24), nullable=False)
    end_lng = db.Column(db.Float(24), nullable=False)
    end_name = db.Column(db.String(200), nullable=True)
    end_number = db.Column(db.String(50), nullable=True)
    end_street = db.Column(db.String(100), nullable=True)
    end_city = db.Column(db.String(50), nullable=False)
    end_state = db.Column(db.String(15), nullable=False) #add validation
    end_zip = db.Column(db.Integer, nullable=False)

    # Date/Time
    start_timestamp = db.Column(db.DateTime, nullable=False)
    end_timestamp = db.Column(db.DateTime, nullable=False)
   
    
    #Details
    mileage = db.Column(db.Float(24), nullable=True)   # would there be a way to validate this? API?
    luggage =  db.Column(db.String(50), nullable=True) #number for now.. drop down js
    comments = db.Column(db.Text, nullable=True) #db.Text field??
    pickup_window = db.Column(db.String(50), nullable=True) 
    detour = db.Column(db.String(50), nullable=True) 
    car_type = db.Column(db.String(100), nullable=True)


    user = db.relationship("User",
                            backref=db.backref("rides_offered"))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Ride ride_id={}, driver={}, start={}, end={}, date={}>".format(self.ride_id, 
            self.driver, self.start_city, self.end_city, self.start_timestamp)

class Rider(db.Model):
    """Association table. Users taking Rides"""

    __tablename__ = "riders"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.ride_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    seats = db.Column(db.Integer, nullable=False)

    user = db.relationship("User",
                            backref=db.backref("rides_taking"))

    ride = db.relationship("Ride",
                            backref=db.backref("riders"))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Rider id={}, ride_id={}, user_id={}>".format(self.id, 
            self.ride_id, self.user_id)


class Request(db.Model):
    """Requests for rides"""

    __tablename__ = "requests"

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.ride_id'), nullable=False)
    requester = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    seats = db.Column(db.Integer, nullable=False)


    ride = db.relationship("Ride",
                            backref=db.backref("requests"))

    user = db.relationship("User",
                            backref=db.backref("requests"))

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Requests id={}, ride_id={}, requester={}, seats={}>".format(self.id, 
            self.ride_id, self.requester, self.seats)

# class Request(db.Model):
#     """Pending Requests"""

#     id = db.Column(db.Integer, nullable=False, autoincrement=True, primary_key=True)
#     ride_id = db.Column(db.Integer, nullable=False, db.ForeignKey('riders.ride_id'))
#     user_id = db.Column(db.Integer, nullable=False, db.ForeignKey('users.user_id'))
#     seats = db.Column(db.Integer, nullable=False)

#  id | ride_id | user_id | seats 
# ----+---------+---------+-------
#   1 |       1 |       3 |     2
#   2 |       1 |       4 |     2
#   3 |       2 |       1 |     1
#   4 |       2 |       4 |     1
# (4 rows)

# rideshare=# select * from users;
#  user_id |  name  |  email  | password 
# ---------+--------+---------+----------
#        1 | Maddie | maddie@ | doge1
#        2 | Ahmad  | ahmad@  | doge2
#        3 | Carl   | carl@   | doge3
#        4 | Lexie  | lexie@  | doge4
# (4 rows)

#  ride_id | driver | start_location | end_location |            date            | seats 
# ---------+--------+----------------+--------------+----------------------------+-------
#        1 |      1 | SF             | Tahoe        | 2016-10-31 22:47:41.647222 |     4
#        2 |      2 | SF             | LA           | 2016-10-31 22:47:41.647333 |     4
#        3 |      1 | NY             | SF           | 2016-11-05 00:00:00        |     5
#        4 |      2 | SF             | Tahoe        | 2016-12-25 00:00:00        |     5













##############################################################################
# Helper Functions

def connect_db(app):
    """Connect db to Flask app"""

    # Configure connection to PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///rideshare'
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)

if __name__ == "__main__":

    from server import app
    connect_db(app)
    print "Connected to Database"