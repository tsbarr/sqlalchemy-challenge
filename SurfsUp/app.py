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

# Find the most recent date in the data set.
# We can use func.max to find the biggest date
most_recent_date = session.query(func.max(Measurement.date)).all()
# Convert most recent date to a date object
most_recent_date = pd.to_datetime(most_recent_date[0][0]).date()
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
    <ul>
        <li>/api/v1.0/&lt;start&gt;</li>
        <li>/api/v1.0/&lt;start&gt;/&lt;end&gt;</li>
    </ul>

    '''

# Define what to do when a user hits the /api/v1.0/precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
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
    print("Server received request for 'precipitation' page...")
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


# Close Session
session.close()


if __name__ == "__main__":
    app.run(debug=True)
