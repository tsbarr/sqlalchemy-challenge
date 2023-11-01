# Import the dependencies.
from flask import Flask, jsonify
# import numpy as np
import pandas as pd
# import datetime as dt
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
        <li>/api/v1.0/<start></li>
        <li>/api/v1.0/<start>/<end></li>
    </ul>

    '''

# Define what to do when a user hits the /api/v1.0/precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Find the most recent date in the data set.
    # We can use func.max to find the biggest date
    most_recent_date = session.query(func.max(Measurement.date)).all()
    # Convert most recent date to a date object
    most_recent_date = pd.to_datetime(most_recent_date[0][0]).date()
    lower_limit_date = most_recent_date.replace(year=most_recent_date.year - 1)
    # Perform a query to retrieve the date and precipitation scores
    date_and_precipitation = (session
        .query(Measurement.date, Measurement.prcp)
        .filter(Measurement.date >= lower_limit_date)
        .all()
    )
    prcp_dict = {}
    for row in date_and_precipitation:
        prcp_dict[row[0]]: row[1]
    return jsonify(prcp_dict)


# Define what to do when a user hits the /api/v1.0/stations route
@app.route("/api/v1.0/stations")
def stations():
    stations_query = (session
        .query(Station.station, Station.name)
        .all()
    )
    stations_list = []
    for row in stations_query:
        this_station = {
            'station': row[0],
            'name': row[1]
        }
        stations_list.append(this_station)
    return jsonify(stations_list)






if __name__ == "__main__":
    app.run(debug=True)
