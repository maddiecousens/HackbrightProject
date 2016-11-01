""" Rideshare App """

from jinja2 import StrictUndefined

from flask import (Flask, jsonify, render_template, redirect, 
                   request, flash, session)

from flask_debugtoolbar import DebugToolbarExtension

from model import User, Ride, Rider, Request

from datetime import datetime



app = Flask(__name__)

# Secret key - required for Flask Sessions and debug toolbar
app.secret_key = "thomothgromoth"

# Fail if Jinja uses undefined variable
app.jinja_env.undefined = StrictUndefined

#############################################################################
# Routes

@app.route('/')
def index():
    """ Homepage """

    return render_template('index.html', session=session)

@app.route('/search')
def search_rides():
    """Search database for rides"""

    # If user clicks 'All Rides' from NavBar, show all rides
    if request.args.get('query'):
        rides = Ride.query.options(db.joinedload('user')).all()
        return render_template('search.html', rides=rides, session=session)

    # If user enters search terms, show rides based off search terms
    else:
        starting = request.args.get('starting')
        ending = request.args.get('ending')

        rides = Ride.query.options(db.joinedload('user')).filter(Ride.start_location == starting, Ride.end_location == ending).all()
        
        return render_template('search.html', rides=rides, session=session)

@app.route('/post-ride', methods=["GET"])
def view_rideform():
    """ Form to post new ride """

    return render_template('rideform.html', session=session)

@app.route('/post-ride', methods=["POST"])
def process_rideform():
    """ Add new ride to database """

    # Get driver from who is logged in
    driver = session['current_user']

    start_location = request.form.get('start_location')
    end_location = request.form.get('end_location')
    # parse date
    date = datetime.strptime(request.form.get('date'),'%m/%d/%y')
    seats = request.form.get('seats')

    ride = Ride(driver=driver, start_location=start_location, end_location=end_location, date=date, seats=seats)

    db.session.add(ride)
    db.session.commit()

    flash("Ride added to DB")

    return redirect('/')


@app.route('/login', methods=["GET"])
def view_login():
    """ Show login form """
    return render_template('login.html', session=session)

@app.route("/login", methods=["POST"])
def login_process():
    """ Process login """

    # Get email and password from input fields in form
    email = request.form.get('email')
    password = request.form.get('password')


    # If email is in database, grab password from database
    if User.query.filter(User.email == email).first():

        # Grab user OBJECT
        user = User.query.filter(User.email==email).first()

        db_password = user.password

        # Check if provided pw matches db pw
        if password == db_password:

            # Set session cookie to user_id from user OBJECT
            session['current_user'] = user.user_id 
            flash("Logged in as %s" % user.name)
            redirect_path = '/profile/{}'.format(user.user_id)
            return redirect(redirect_path) 

        # If wrong password, flash message, redirect to login
        else:
            flash("Wrong password!")
            return redirect("/login")

    # If email is not in database, flash message, redirect to /login
    else:
        flash("Email is not in use.  Please register.")
        return redirect("/login")

    # QUESTION : how do I redirect them from whatever page they logged in from?
    #   ideas: keep stored in sessions what page the request is coming from

@app.route('/logout', methods=["GET"])
def logout_form():
    """ Temporary logout form """

    return render_template('logout.html', session=session)


@app.route('/logout', methods=["POST"])
def logout():
    """ Log out user """

    # delete session
    del session['current_user']
    flash("You've been logged out")

    return redirect("/")


@app.route('/register', methods=["GET"])
def register_form():
    """ Registration form """

    return render_template('register.html', session=session)

@app.route('/register', methods=["POST"])
def register():
    """Add new user to database """

    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    user = User(name=name, email=email, password=password)

    db.session.add(user)
    db.session.commit()
    flash("You have been added as a user. Please login")

    return redirect("login")


@app.route('/profile/<user_id>', methods=["GET"])
def user_profile(user_id):
    """ Show users home page """
    # Eventually will make this so that you can view your drivers page too

    user = User.query.options(db.joinedload('rides_taking'), db.joinedload('rides_offered')).get(user_id)
    rides_offered = user.rides_offered
    # request_objects = []
    # for ride in rides_offered:
    #     if ride.requests:
    #         request_objects.append

    rides_taking = user.rides_taking

    return render_template('profile.html', session=session, 
                                           user=user, 
                                           rides_offered=rides_offered, 
                                           rides_taking=rides_taking)

@app.route('/request-seats', methods=["POST"])
def request_seats():
    """ Add request for a seat to database """
    
    # Grab number of seats requested
    seats = request.form.get('seats')

    # Grab ride_id from html
    ride_id = request.form.get('ride_id')

    # Grab requester from session
    requester = session['current_user']

    # Make request instance
    new_request = Request(ride_id=ride_id, requester=requester, seats=seats)

    db.session.add(new_request)
    db.session.commit()
    flash('You have requested this ride')

    path = '/profile/{}'.format(requester)
    return redirect(path)


@app.route('/request-approval', methods=["POST"])
def request_approval():
    """Approve or reject request"""

    # Grab whether the approve or deny request was clicked
    approval = request.form.get('approvedeny')

    # Grab other information from html/session
    ride_id = request.form.get('ride_id')
    requester = request.form.get('requester')
    seats = request.form.get('seats')
    request_id = request.form.get('request_id')
    current_user = session['current_user']

    # If request is approved
    if approval == 'Approve':
        # Query for Request object
        ride_request = Request.query.get(request_id)

        # Query for Ride object
        ride = Ride.query.get(ride_id)
        # Subtract number of seats from Ride
        ride.seats = ride.seats - int(seats)

        # Create new Rider object
        rider = Rider(ride_id=ride_id, user_id=requester, seats=seats)

        # Delete Request Row
        db.session.delete(ride_request)
        db.session.add(rider)
        db.session.commit()

        flash("Request Approved")

    # If request is rejected
    else:
        # Query for Request object
        ride_request = Request.query.get(request_id)

        # Delete Request
        db.session.delete(ride_request)
        db.session.commit()
        flash("Request Denied")

    path = '/profile/{}'.format(current_user)
    return redirect(path)

#### Future Routes ####
# @app.route('/details/<rideid>')
# def ride_details():
#     return render_template('details.html', ride_id=ride_id)


if __name__ == '__main__':
    # Debug for DebugToolbarExtension. Also so server restarts when changes made
    app.debug = True

    # Connection function from model.py
    connect_db(app)

    # Debug Toolbar
    DebugToolbarExtension(app)

    # Allows redirects
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

    app.run(host="0.0.0.0", port=5000)
    # app.run(debug=True, host="0.0.0.0")