from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from .charts import Chart, ChartSet
from .models import USDatum, StateDatum, CountyDatum, State, County
from .db import get_db
from sqlalchemy.orm import joinedload

bp = Blueprint('covid', __name__)
db = get_db()

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

@bp.route('/')
def index():
    us = request.args.get('us')
    states = request.args.get('states')
    counties = request.args.get('counties')    

    us_chartset = get_us_chartset(us)
    state_chartset = get_state_chartset(states)
    county_chartset = get_county_chartset(counties)
    
    return render_template('covid/index.html', us_chartset=us_chartset, state_chartset=state_chartset, county_chartset=county_chartset)