# Import the dependencies.
from flask import Flask, jsonify
# import numpy as np
import pandas as pd
# Python SQL toolkit and Object Relational Mapper
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, desc

#################################################
# Database Setup
#################################################
# Create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

# Define function to use in both dynamic routes
def start_end_tobs(start, end):
    # Try to convert start to date type
    try:
        start = pd.to_datetime(start).date()
    # if date is out of bounds, find the closest option
    except pd._libs.tslibs.np_datetime.OutOfBoundsDatetime:
        min_date = session.query(func.min(Measurement.date)).all()
        # Convert to a date object
        start = pd.to_datetime(min_date[0][0]).date()
    # Try to convert end to date type
    try:
        end = pd.to_datetime(end).date()
    # if date is out of bounds, find the closest option
    except pd._libs.tslibs.np_datetime.OutOfBoundsDatetime:
        # Use most_recent_date
        end = most_recent_date
    # Query filtering desired dates
    query_results = (session
        .query(
            func.min(Measurement.tobs),
            func.max(Measurement.tobs),
            func.avg(Measurement.tobs),
        )
        .filter(Measurement.date >= start)
        .filter(Measurement.date <= end)
        .all()
        )
    # Put results into a dictionary
    result_dict = {
            'min_tobs': query_results[0][0],
            'max_tobs': query_results[0][1],
            'avg_tobs': query_results[0][2]
        }
    return result_dict

# Define variables used in more than one route ---

# Find the most recent date in the data set.
# We can use func.max to find the biggest date
most_recent_date = session.query(func.max(Measurement.date)).all()
# Convert most recent date to a date object
most_recent_date = pd.to_datetime(most_recent_date[0][0]).date()
# Find date that is one year before most_recent_date
lower_limit_date = most_recent_date.replace(year=most_recent_date.year - 1)

# Find the most active station by querying station activity
station_activity = (session
    .query(
        Station.station,
        func.count(Measurement.id).label('count')
    )
    .filter(Measurement.station == Station.station)
    .group_by(Station.station)
    .order_by(desc('count'))
    .all()
)
# Most active station is the first result
most_active_station = station_activity[0][0]

#################################################
# Flask Setup
#################################################
# Create app, passing __name__
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
# Define what to do when a user hits the index route
@app.route("/")
def home():
    # html showing available routes
    print("Server received request for 'Home' page...")
    return '''
    <h2>Welcome to the Hawaii Climate API!</h2>

    <p>Available static routes:</p>
    <ul>
        <li>/api/v1.0/precipitation</li>
        <li>/api/v1.0/stations</li>
        <li>/api/v1.0/tobs</li>
    </ul>
    <p>Available dynamic routes:</p>
    <p>Note that &lt;start&gt; and &lt;end&gt; stand for date parameters to limit the results.<br/>They should be entered using YYYY-MM-DD format.<br/>If using dates that are out of bounds, the results returned use the most recent date as end point and the earliest date as start point.</p>
    <ul>
        <li>/api/v1.0/&lt;start&gt;</li>
        <li>/api/v1.0/&lt;start&gt;/&lt;end&gt;</li>
    </ul>

    '''

# Define what to do when a user hits the /api/v1.0/precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for 'precipitation' page...")
    # Perform a query to retrieve the date and precipitation scores
    prcp_query = (session
        .query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= lower_limit_date)
        .all()
        )
    # Create dictionary to store values
    prcp_dict = {}
    # Loop through query results
    for row in prcp_query:
        # Get values from current row
        this_date = row[0]
        this_prcp = row[1]
        # Try to append prcp value to dict key that is this date
        try:
            prcp_dict[this_date].append(this_prcp)
        # Catch if key doesn't exist
        except KeyError:
            # In which case, create key this_date
            #  with value of a list with one element: this_prcp
            prcp_dict[this_date] = [this_prcp]
    return jsonify(prcp_dict)


# Define what to do when a user hits the /api/v1.0/stations route
@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for 'stations' page...")
    # Query to find all station names and station id
    stations_query = (session
        .query(Station.station, Station.name)
        .all()
    )
    # Create empty list to store data
    stations_list = []
    # Loop through query results
    for row in stations_query:
        # Create dict for current row's station
        this_station = {
            'station': row[0],
            'name': row[1]
        }
        # Add to stations_list
        stations_list.append(this_station)
    return jsonify(stations_list)

# Define what to do when a user hits the /api/v1.0/tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for 'tobs' page...")
    # Query to find tobs data for most_active_station for prev year
    tobs_query = (session
                .query(Measurement.tobs)
                .filter(Measurement.date >= lower_limit_date)
                .filter(Measurement.station == most_active_station)
                .all()
                )
    # Loop through query results and put tobs values into a list
    tobs_list = [row[0] for row in tobs_query]
    return jsonify(tobs_list)

# Define what to do when a user hits the /api/v1.0/<start> route
@app.route("/api/v1.0/<start>")
def start(start):
    print(f"Server received request for 'start' page with start = {start}...")
    # use most_recent_date as end date
    start_dict = start_end_tobs(start, most_recent_date)
    return jsonify(start_dict)

# Define what to do when a user hits the /api/v1.0/<start>/<end> route
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    print(f"Server received request for 'start/end' page with start = {start}, and end = {end}...")
    # use provided dates
    start_end_dict = start_end_tobs(start, end)
    return jsonify(start_end_dict)

# Close Session
session.close()


if __name__ == "__main__":
    app.run(debug=True)
