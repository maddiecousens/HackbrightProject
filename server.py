""" Rideshare App """

from jinja2 import StrictUndefined

from flask import (Flask, jsonify, render_template, redirect, request, flash, 
                   session)
from sqlalchemy import cast, Time
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Ride, Rider, Request, connect_db, db

from datetime import datetime, date, timedelta, time
import pytz

import geocoder

from helperfunctions import state_to_timezone, miles_to_degrees

import os
import googlemaps


app = Flask(__name__)

# Secret key - required for Flask Sessions and debug toolbar
app.secret_key = "thomothgromoth"

# Fail if Jinja uses undefined variable
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True

GOOGLE_KEY = os.environ["GOOGLE_KEY"]

#############################################################################
# Routes

@app.route('/')
def index():
    """ Homepage """

    return render_template('index.html')

##################################                               
####### Searching Routes #########
##################################

@app.route('/search')
def search_rides():
    """Searches database for rides"""

    # If user clicks 'All Rides' from NavBar, show all rides
    if request.args.get('query'):

        # Query database for all rides
        rides = Ride.get_rides(limit=10, order_by='date')
        page_count = int(Ride.query.count()) / 10
        # rides = (Ride.query.options(db.joinedload('user'))
        #                    .order_by(Ride.start_timestamp).all())
        
        # Create dicts to hold search parameters that will be added to html 
        #   and Utilized by AJAX when search results are toggled.
        gmaps = googlemaps.Client(key=GOOGLE_KEY)

        for ride in rides:
            # Convert to local time for start state
            ###############
            ## to do: should really be the users timezone, since rides could
            ## significantly vary by timezone when searching all rides. ADJUST
            ################


            ride.start_timestamp = to_local(ride.start_state, ride.start_timestamp)

            # print '\n\n',ride,'\n\n'

            # print '\n**{}\n'.format(ride.start_timestamp)
            ride.start_timestamp = to_time_string(ride.start_timestamp)

            
            db.session.commit()
        return render_template('search.html', rides=rides, page_count=page_count)

    # If user enters search terms, show rides based off search terms
    else:
 
        # Eventually add miles as an input field
        miles = 25
        count = 0

        # Convert miles to lat/lng degrees
        deg = miles_to_degrees(miles)
        
        # Get search terms lat/lng
        start_lat = float(request.args.get('lat'))
        start_lng = float(request.args.get('lng'))
        end_lat = float(request.args.get('lat2'))
        end_lng = float(request.args.get('lng2'))

        # Create dicts to hold search parameters that will be added to html 
        #   and Utilized by AJAX when search results are toggled.
        start_search = {"term": request.args.get('searchstring'),
                        "state": request.args.get('administrative_area_level_1'),
                        "lat": start_lat,
                        "lng": start_lng
                       }
        end_search = {"term": request.args.get('searchstring2'),
                      "state": request.args.get('administrative_area_level_1_2'),
                      "lat": end_lat,
                      "lng": end_lng
                      }

        rides = Ride.get_rides(deg=deg, start_lat=start_lat, start_lng=start_lng,
                               end_lat=end_lat, end_lng=end_lng)

        for ride in rides:
            count += 1
            # Convert timestamp to local time
            ride.start_timestamp = to_local(ride.start_state, ride.start_timestamp)

            ride.start_timestamp = to_time_string(ride.start_timestamp)

        return render_template('search.html', rides=rides,
                                              start_search=start_search,
                                              end_search=end_search, 
                                              count=count)

@app.route('/search-time.json')
def json_test():
    """Return new ride results"""

    #Get location search terms

    start_term = request.args.get('start_term')
    end_term = request.args.get('end_term')

    user_lat = request.args.get('user_lat')
    user_lng = request.args.get('user_lng')

    start_lat = request.args.get('start_lat')
    start_lng = request.args.get('start_lng')
    end_lat = request.args.get('end_lat')
    end_lng = request.args.get('end_lng')
    start_state = request.args.get("start_state")

    # Get search toggles (time, cost, date)

    start_time = request.args.get("start")
    cost = request.args.get("cost")

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    limit = request.args.get("limit")
    offset = request.args.get("offset")
    order = request.args.get("order")

    if date_from:
        date_from = to_utc_date(start_state, date_from)

    if date_to:
        date_to = to_utc_date(start_state, date_to)


    # Convert miles to lat/lng degrees
    deg = miles_to_degrees(25)

    # If no location is specified
    if not(start_term) and not(end_term):
        client_state = (geocoder.google('{}, {}'.format(user_lat, user_lng))).state
        # print '\n\n{}\n\n'.format(client_state, user_lat, )
        start_time = to_utc_time(client_state, start_time)
    else:
        start_time = to_utc_time(start_state, start_time)



    rides = Ride.get_rides(deg=deg, 
                           start_lat=start_lat,
                           start_lng=start_lng,
                           end_lat=end_lat,
                           end_lng=end_lng,
                           start_time=start_time,
                           cost=cost,
                           date_to=date_to,
                           date_from=date_from,
                           limit=limit, #################
                           offset=offset,
                           order=order)

    total_count = Ride.get_rides(deg=deg, 
                               start_lat=start_lat,
                               start_lng=start_lng,
                               end_lat=end_lat,
                               end_lng=end_lng,
                               start_time=start_time,
                               cost=cost,
                               date_to=date_to,
                               date_from=date_from,
                               count=True)

    # print '\n\n{}\n\n'.format(total_count)
    json_list = sqlalchemy_to_json(rides, total_count, limit)

    return jsonify(json_list)



##################################                               
######### Testing Route ##########
##################################


@app.route('/googletest', methods=["GET"])
def google_test():
    """  """
    count = 6
    return render_template('slider.html', count=count)

##################################                               
######## Post Ride Form ##########
##################################

@app.route('/post-ride', methods=["GET"])
def view_rideform():
    """ Form to post new ride """

    return render_template('rideform.html')

@app.route('/post-ride', methods=["POST"])
def process_rideform():
    """ Add new ride to database """
    
    ###############
    ## to do: 
    ##- Add logged in check
    ##- DON'T ADD TO DB IF THE FIELDS ARE BLANK!!!
    ################
    user = session['current_user']
    driver = session['current_user']

    ###### Store Auto Completed Addresses ########

    start_string = request.form.get('start-address')
    start_lat = request.form.get('lat')
    start_lng = request.form.get('lng')
    start_number = request.form.get('street_number')
    start_street = request.form.get('route')
    start_city = request.form.get('locality')
    start_state = request.form.get('administrative_area_level_1')
    start_zip = request.form.get('postal_code')

    end_string = request.form.get('end-address')
    end_lat = request.form.get('lat2')
    end_lng = request.form.get('lng2')
    end_number = request.form.get('street_number2')
    end_street = request.form.get('route2')
    end_city = request.form.get('locality2')
    end_state = request.form.get('administrative_area_level_1_2')
    end_zip = request.form.get('postal_code2')


    ##### Other Data ######

    cost = request.form.get('cost')
    seats = int(request.form.get('seats'))
    
    luggage = request.form.get('luggage')
    comments = request.form.get('comments')
    pickup_window = request.form.get('pickup-window')
    detour = request.form.get('detour')
    car_type = request.form.get('cartype')

    ####### PARSE datetime from datetimepicker ########

    start_time = datetime.strptime(request.form.get('date1'), "%m/%d/%Y %I:%M %p")
    end_time = datetime.strptime(request.form.get('date2'), "%m/%d/%Y %I:%M %p")

    # Convert to utc

    start_time = to_utc_datetime(start_state, start_time)
    end_time = to_utc_datetime(end_state, end_time)


    ######## Create Ride Instance ############

    # import pdb; pdb.set_trace()

    ride = Ride(driver=driver,
                seats=seats,
                cost=cost,
                # starting location
                start_lat=start_lat,
                start_lng=start_lng, #eventually change to lng
                start_number=start_number,
                start_street=start_street,
                start_city=start_city,
                start_state=start_state,
                start_zip=start_zip,
                # ending location
                end_lat=end_lat,
                end_lng=end_lng,
                end_number=end_number,
                end_street=end_street,
                end_city=end_city,
                end_state=end_state,
                end_zip=end_zip,
                #details
                start_timestamp=start_time,
                end_timestamp=end_time,

                car_type=car_type,
                luggage=luggage,
                comments=comments,
                pickup_window=pickup_window,
                detour=detour
               )

    db.session.add(ride)
    db.session.commit()

    flash("Ride added to DB")

    return redirect('/profile/{}'.format(user)) 

##################################                               
##### Login/Logout/Register ######
##################################

@app.route('/login', methods=["GET"])
def view_login():
    """ Show login form """
    return render_template('login.html')


@app.route("/login2", methods=["POST"])
def fb_login_process():
    """ Facebook Process login """
    fb_userid = request.form.get("id")
    fb_user_accesstoken = request.form.get('access_token')

    # if User.query.filter(User.email == email).first():

    #     # Grab user OBJECT
    #     user = User.query.filter(User.email==email).first()

    #     db_password = user.password

    #     # Check if provided pw matches db pw
    #     if password == db_password:

    #         # Set session cookie to user_id from user OBJECT
    #         session['current_user'] = user.user_id 
    #         flash("Logged in as %s" % user.first_name)
    #         redirect_path = '/profile/{}'.format(user.user_id)
    #         return redirect(redirect_path) 

    #     # If wrong password, flash message, redirect to login
    #     else:
    #         flash("Wrong password!")
    #         return redirect("/login")

    # # If email is not in database, flash message, redirect to /login
    # else:
    #     flash("Email is not in use.  Please register.")
    #     return redirect("/login")



    print '\n\n',fb_userid, fb_user_accesstoken,'\n\n'

    return "hi"



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
            flash("Logged in as %s" % user.first_name)
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
    """ Log user out"""

    del session['current_user']
    flash("You've been logged out")

    return redirect("/")

@app.route('/register', methods=["GET"])
def register_form():
    """ Registration form """

    return render_template('register.html')

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

##################################                               
#### Profile Page + Requests #####
##################################


@app.route('/profile/<user_id>', methods=["GET"])
def user_profile(user_id):
    """ Show users home page """
    # Eventually will make this so that you can view your drivers page too

    user = User.query.options(db.joinedload('rides_taking'), db.joinedload('rides_offered')).get(user_id)
    rides_offered = user.rides_offered

    rides_taking = user.rides_taking

    return render_template('profile.html', user=user, 
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

### Helper Functions ###

def sqlalchemy_to_json(rides, total_count, limit):
    """Convert sqlalchemy objects to json"""

    attributes = ['car_type',
                 'comments',
                 'cost',
                 'detour',
                 'driver',
                 'duration',
                 'end_city',
                 'end_lat',
                 'end_lng',
                 'end_name',
                 'end_number',
                 'end_state',
                 'end_street',
                 'end_timestamp',
                 'end_zip',
                 'luggage',
                 'mileage',
                 'pickup_window',
                 'ride_id',
                 'seats',
                 'start_city',
                 'start_lat',
                 'start_lng',
                 'start_name',
                 'start_number',
                 'start_state',
                 'start_street',
                 'start_timestamp',
                 'start_zip']

    # Instantiate list
    json_list = []

    # iterate over  and add to temp_dict
    for ride in rides:

        temp_dict = {}
        for attr in attributes:
            temp_dict[attr] = getattr(ride, attr)
        
        # Convert timestamp to local, add as string to temp_dict
        ride.start_timestamp = to_local(ride.start_state, ride.start_timestamp)
        temp_dict['start_timestamp'] = to_time_string(ride.start_timestamp)

        # Add driver info, utilizing SQLAlchemy relationships
        temp_dict['user_first_name'] = ride.user.first_name
        temp_dict['user_image'] = ride.user.image
        
        json_list.append(temp_dict)

    page_count = int(total_count) / int(limit)
    # print '\n\nPage count: {}\n\n'.format(page_count)
    json_list_final = [{'page_count': page_count}]
    json_list_final.append(json_list)
    return json_list_final

def to_utc_time(state, start_time):
    """Convert unaware time to UTC"""
    # Convert time to datetime object without tz
    start_time_notz = datetime.strptime(start_time, '%I:%M %p')
    # Get timezone of ride's starting state
    tz = state_to_timezone(state)
    # Localize to timezone of state the ride is leaving from
    start_time_aware = pytz.timezone(tz).localize(start_time_notz)
    # Normalize to UTC in order to search DB
    start_time_utc = pytz.utc.normalize(start_time_aware)
    # Use time() method to create a time only object
    return start_time_utc.time()

def to_utc_date(state, date_str):

    # Convert date string into datetime object without tz
    date_notz = datetime.strptime(date_str, '%m/%d/%Y')
    # Get timezone of starting state or user's state
    tz = state_to_timezone(state)
    # Localize to timezone of state the ride is leaving from
    date_aware = pytz.timezone(tz).localize(date_notz)
    # Normalize to UTC in order to search DB
    date_utc = pytz.utc.normalize(date_aware)
    # Use time() method to create a time only object
    return date_utc.date()


def to_utc_datetime(state, timestamp):
    """Convert datetime object to utc datetime object"""
    tz = state_to_timezone(state)

    # Localize timezone
    timestamp_aware = pytz.timezone(tz).localize(timestamp) 

    # Convert to utc
    timestamp_utc = pytz.utc.normalize(timestamp_aware)

    return timestamp_utc

def to_local(state, timestamp):
    """Convert UTC to local time"""
    # Use state from database to determine timezone
    tz = state_to_timezone(state)
    # Convert timestamp from db to be aware that it is in utc
    utc = timestamp.replace(tzinfo=pytz.utc)
    # Convert start_timestamp attribute to timezone of state
    local = pytz.timezone(tz).normalize(utc)

    return local

def to_time_string(timestamp):
    # If ride is today, adjust attribute to indicate
    ###############
    ## to do: compare to user's TZ not US/Pacific
    ################

    today = datetime.now(pytz.timezone('US/Pacific')).date()

    if timestamp.date() == today:
        datetime_str = "Today, {}".format(timestamp.strftime('%-I:%M %p'))

    # If ride is tomorrow, adjust attribute to indicate
    elif timestamp.date() == (today + timedelta(days=1)):
        datetime_str = "Tomorrow, {}".format(timestamp.strftime('%-I:%M %p'))
    # Otherwise change attribute to formatted timestamp string
    else:
        datetime_str = timestamp.strftime('%A, %b %d, %Y %-I:%M %p')

    return datetime_str


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