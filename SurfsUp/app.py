# Import the dependencies.
import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect, text

import datetime as dt

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

#create engine
engine = create_engine("sqlite:///hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
sessions = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def usage():
    return """
    Available routes:<br/>
    /api/v1.0/precipitation<br/>
    /api/v1.0/stations<br/>
    /api/v1.0/tobs<br/>
    /api/v1.0/tstats/&lt;start&gt;<br/>
    /api/v1.0/tstats/&lt;start&gt;/&lt;end&gt; 
    """

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    with Session(bind=engine) as sessions:
        # Query past 12 months of precipitation data.
        recent_year = sessions.query(measurement.prcp, measurement.date).\
            filter(measurement.date >= year_ago_str).\
            filter(measurement.date <= recent_date_str).\
            order_by(measurement.date).all()
        # Convert results of query into a dictionary
        # The key will be the date, the value will be the temp readings in a list since each date has several temp readings (readings taken same day at different stations).
        precipitation_dict = {}
        previous_date = ""
        for date in recent_year:
            current_date = date[1]
            if current_date != previous_date:
                precipitation_dict[current_date] = []
                precipitation_dict[current_date].append(date[0])
                previous_date = current_date  
            else:
                precipitation_dict[current_date].append(date[0])
                previous_date = current_date              
        # Return the JSON representation of your dictionary
        return jsonify(precipitation_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    with Session(bind=engine) as sessions:
        # Return a JSON list of stations from the dataset.
        stations_query = sessions.query(station.name).all()
        all_stations = list(np.ravel(stations_query))
        return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    with Session(bind=engine) as sessions:
        # Find the most active station
        station_activity = sessions.query(measurement.station, func.count(measurement.station)).\
            group_by(measurement.station).\
            order_by((func.count(measurement.station)).desc()).\
            all()
        most_active = list(np.ravel(station_activity))
        most_active = most_active[0]
        # Query the dates and temperature observations of the most-active station for the previous year of data.
        most_active_query = sessions.query(measurement.tobs, measurement.date).\
            filter(measurement.station == most_active).\
            filter(measurement.date >= year_ago_str).\
            filter(measurement.date <= recent_date_str).\
            order_by((measurement.date).asc()).all()
        # Convert results of query into a dictionary
        most_active_temps = {}
        for date in most_active_query:
            most_active_temps[date[1]] = date[0]
        # Return the JSON representation of your dictionary
        return jsonify(most_active_temps)
    
@app.route("/api/v1.0/tstats/<start>")    
@app.route("/api/v1.0/tstats/<start>/<end>")
def tstats(start, end=None):
    # Autocomplete end date if not given by user
    if not end:
        end = dt.date.max
    # Create our session (link) from Python to the DB
    with Session(bind=engine) as sessions:
        # For a specified start date and end date, calculate TMIN, TAVG, and TMAX for the dates from the start date to the end date, inclusive.
        start_end_query = sessions.query(func.min(measurement.tobs), func.max(measurement.tobs), func.avg(measurement.tobs)).\
            filter(measurement.date >= start).\
            filter(measurement.date <= end).all()
        start_end_data = list(np.ravel(start_end_query))
        return jsonify(start_end_data)

if __name__ == "__main__":
    app.run(debug=True)

# Close Session
sessions.close()