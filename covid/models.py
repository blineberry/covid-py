from .db import db

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