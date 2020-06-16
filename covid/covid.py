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

    try:
        count = int(count)
    except:
        return []
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
        try:
            id = int(state_id)
        except:
            continue
        data = db.session.query(StateDatum).filter_by(state_id=id).order_by('date').options(joinedload(StateDatum.state)).all()
        chartset.add_chart(Chart(data, name=data[0].state.name))

    return chartset


def get_county_chartset(counties):
    if counties is None:
        return []

    counties = counties.split(',')

    chartset = ChartSet()

    for county_id in counties:
        try:
            id = int(county_id)
        except:
            continue
        data = db.session.query(CountyDatum).filter_by(county_id=id).order_by('date').options(joinedload(CountyDatum.county).joinedload(County.state)).all()
        chartset.add_chart(Chart(data, name="{}, {}".format(data[0].county.name, data[0].county.state.name)))

    return chartset

def try_parse_int(str):
    try:
        return int(str)
    except:
        return None

@bp.route('/')
def index():
    us = request.args.get('us', default='', type=str)
    states = request.args.get('states', default='', type=str)
    counties = request.args.get('counties', default='', type=str)    

    us_chartset = get_us_chartset(us)
    state_chartset = get_state_chartset(states)
    county_chartset = get_county_chartset(counties)
    
    return render_template(
        'covid/index.html', 
        us_chartset=us_chartset, 
        state_chartset=state_chartset, 
        county_chartset=county_chartset,
        selected_us=us,
        selected_states=states,
        selected_counties=counties)

@bp.route('/select', methods=('GET', 'POST'))
def select_charts():
    if request.method == 'POST':
        us = request.form.get('us')
        states = request.form.getlist('states')
        counties = request.form.getlist('counties')
        return redirect(url_for('.index', us=us,states=",".join(states),counties=",".join(counties)))


    states_selected = [try_parse_int(s) for s in request.args.get('states', default='', type=str).split(',')]
    counties_selected = [try_parse_int(c) for c in request.args.get('counties', default='', type=str).split(',')]

    print(counties_selected)

    states = db.session.query(State).order_by('name').options(joinedload(State.counties)).all()
    return render_template('covid/select.html', states=states, us_selected=request.args.get('us', default=0, type=int), state_selected=states_selected, counties_selected=counties_selected)