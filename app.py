from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
from datetime import datetime

app = Flask(__name__)

app.config.from_pyfile('settings.py')
db = SQLAlchemy(app)

def get_us_chartset(count):
    if count is None:
        return []

    count = int(count)
    chartset = ChartSet()

    data = db.session.query(USDatum).order_by('date').all()

    for x in range(0,count):
        chartset.add_chart(Chart(data, name="U.S."))

    return chartset

def get_state_chartset(states):
    if states is None:
        return []

    states = states.split(',')

    chartset = ChartSet()

    for state_id in states:
        data = db.session.query(StateDatum).filter_by(state_id=state_id).order_by('date').options(joinedload(StateDatum.state)).all()
        chartset.add_chart(Chart(data, name=data[0].state.name))

    return chartset


def get_county_chartset(counties):
    if counties is None:
        return []

    counties = counties.split(',')

    chartset = ChartSet()

    for county_id in counties:
        data = db.session.query(CountyDatum).filter_by(county_id=county_id).order_by('date').options(joinedload(CountyDatum.county).joinedload(County.state)).all()
        chartset.add_chart(Chart(data, name="{}, {}".format(data[0].county.name, data[0].county.state.name)))

    return chartset
        

@app.route('/')
def hello_world():
    us = request.args.get('us')
    states = request.args.get('states')
    counties = request.args.get('counties')    

    us_chartset = get_us_chartset(us)
    state_chartset = get_state_chartset(states)
    county_chartset = get_county_chartset(counties)
    
    return render_template('home.html', us_chartset=us_chartset, state_chartset=state_chartset, county_chartset=county_chartset)

class USDatum(db.Model):
    __tablename__ = 'us_data'
    id = db.Column(db.BigInteger, primary_key=True)
    date = db.Column(db.Date)
    cases = db.Column(db.BigInteger)
    deaths = db.Column(db.BigInteger)
    new_cases = db.Column(db.BigInteger)
    seven_day_average_cases = db.Column(db.BigInteger)

class State(db.Model):
    __tablename__ = 'states'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(26))
    fips = db.Column(db.CHAR(2))

class StateDatum(db.Model):
    __tablename__ = 'state_data'
    id = db.Column(db.BigInteger, primary_key=True)
    date = db.Column(db.Date)
    cases = db.Column(db.BigInteger)
    deaths = db.Column(db.BigInteger)
    new_cases = db.Column(db.BigInteger)
    seven_day_average_cases = db.Column(db.BigInteger)
    state_id = db.Column(db.Integer, db.ForeignKey(State.id))
    state = db.relationship('State', backref=db.backref('data', lazy=True))

class County(db.Model):
    __tablename__ = 'counties'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(26))
    fips = db.Column(db.CHAR(5))
    state_id = db.Column(db.Integer, db.ForeignKey(State.id))
    state = db.relationship('State', backref=db.backref('state_data', lazy=True))

class CountyDatum(db.Model):
    __tablename__ = 'county_data'
    id = db.Column(db.BigInteger, primary_key=True)
    date = db.Column(db.Date)
    cases = db.Column(db.BigInteger)
    deaths = db.Column(db.BigInteger)
    new_cases = db.Column(db.BigInteger)
    seven_day_average_cases = db.Column(db.BigInteger)
    county_id = db.Column(db.BigInteger, db.ForeignKey(County.id))
    county = db.relationship('County', backref=db.backref('county_data', lazy=True))



class ChartSet():
    def __init__(self):
        self.charts = []

    def add_chart(self, chart):
        self.charts.append(chart)
    
    def get_max_cases(self):
        max_cases = 0

        for chart in self.charts:
            for datum in chart.data:
                if datum.seven_day_average_cases > max_cases:
                    max_cases = datum.seven_day_average_cases

        return max_cases
    
    def get_max_days(self):
        max_days = 0

        for chart in self.charts:
            l = len(chart.data) 
            if l > max_days:
                max_days = l
        
        return max_days

class Chart():
    def __init__(self, data, name=""):
        self.data = data
        self.name=name
        self.period_of_uncertainty = []
        self.svg_points = []
        self.svg_uncertain_points = []

    def get_data_subset(self, include_last_two_weeks=False):
        subset = []

        start = len(self.data)

        for index,datum in enumerate(self.data):
            if datum.seven_day_average_cases >= 30:
                start = index
                break
        if include_last_two_weeks:
            return self.data[start:]

        last_datum = self.data[-1]

        days_past = (datetime.now().date() - last_datum.date).days

        if days_past > 14:
            return self.data[start:]

        return self.data[start:days_past-14]

    def get_last_two_weeks(self):
        last_datum = self.data[-1]

        days_past = (datetime.now().date() - last_datum.date).days

        if days_past > 14:
            return []

        last_two_weeks = self.data[days_past - 15::]

        return last_two_weeks

    def get_svg_background(self):
        if len(self.data) <= 0:
            return "white"

        peak = 0

        for datum in self.data:
            peak = max(peak, datum.seven_day_average_cases)

        last_two_weeks = self.get_last_two_weeks()
        last_confident_datum = self.data[-len(last_two_weeks)]

        highest_uncertain_cases = 0

        for datum in last_two_weeks:
            highest_uncertain_cases = max(highest_uncertain_cases, datum.seven_day_average_cases)

        reference_cases = max(last_confident_datum.seven_day_average_cases, highest_uncertain_cases)

        if reference_cases < peak / 2:
            return "#BAE8BA"

        if reference_cases < peak * .75:
            return "#BAE0E8"

        if reference_cases < peak * .9:
            return "#F5CE8C"

        return "#E8BABA"

        

@app.template_filter()
def svg_points(data, max_x, max_y, viewport_x, viewport_y, init_x=0):
    points = []

    for index, datum in enumerate(data):
        points.append("{},{}".format((index + init_x) * viewport_x / max_x, viewport_y - (datum.seven_day_average_cases / max_y * viewport_y)))

    return " ".join(points)