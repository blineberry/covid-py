import MySQLdb
import sys
import argparse
import requests
import csv
from io import StringIO
import statistics
from datetime import datetime

NYTIMES_COUNTIES_URL = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
NYTIMES_STATES_URL = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-states.csv"
NYTIMES_US_URL = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv"

def extract(db):
    print('Extracting…')

    print('Fetching NY Times county data')

    response = requests.get(NYTIMES_COUNTIES_URL)
    reader = csv.DictReader(StringIO(response.text))

    counties = list()

    for row in reader:
        counties.append((row['date'], row['county'], row['state'], row['fips'], row['cases'], row['deaths']))

    print('Saving NY Times county data')
    c = db.cursor()
    try:
        c.execute("""TRUNCATE TABLE ny_times_us_counties""")
        c.executemany(
            """INSERT INTO ny_times_us_counties (date, county, state, fips, cases, deaths)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            counties)
            
    except: 
        print("error inserting")
        sys.exit(2)

    c.close()
    db.commit()




    print('Fetching NY Times state data')

    response = requests.get(NYTIMES_STATES_URL)
    reader = csv.DictReader(StringIO(response.text))

    states = list()

    for row in reader:
        states.append((row['date'], row['state'], row['fips'], row['cases'], row['deaths']))

    print('Saving NY Times state data')
    c = db.cursor()
    try:
        c.execute("""TRUNCATE TABLE ny_times_us_states""")
        c.executemany(
            """INSERT INTO ny_times_us_states (date, state, fips, cases, deaths)
            VALUES (%s, %s, %s, %s, %s)""",
            states)
            
    except: 
        print("error inserting")
        sys.exit(2)

    c.close()
    db.commit()




    print('Fetching NY Times US data')

    response = requests.get(NYTIMES_US_URL)
    reader = csv.DictReader(StringIO(response.text))

    data = list()

    for row in reader:
        data.append((row['date'], row['cases'], row['deaths']))

    print('Saving NY Times US data')
    c = db.cursor()
    try:
        c.execute("""TRUNCATE TABLE ny_times_us""")
        c.executemany(
            """INSERT INTO ny_times_us (date, cases, deaths)
            VALUES (%s, %s, %s)""",
            data)
            
    except: 
        print("error inserting")
        sys.exit(2)

    c.close()
    db.commit()

def get_states_from_nytimes_data(db):
    print('Getting States from NY Times data')
    c = db.cursor()
    c.execute("""SELECT DISTINCT state, fips 
    FROM ny_times_us_states""")

    ny_states = c.fetchall()

    print('Saving new States')
    for ny_state in ny_states:
        c.execute("""SELECT id FROM states WHERE fips = %s""", (ny_state[1],))
        if c.fetchone() is None:
            print(format("%s is a new state", ny_state[0]))
            try:
                c.execute("""INSERT INTO states (name, fips)
                VALUES (%s, %s)""",
                record[0], record[1])          
            except Exception as e: 
                print(e)
                sys.exit(2)

    c.close()
    db.commit()

def get_counties_from_nytimes_data(db):
    print('Getting Counties from NY Times data')
    c = db.cursor()
    c.execute("""SELECT DISTINCT county, state, fips 
    FROM ny_times_us_counties""")

    counties = c.fetchall()

    print('Saving new Counties')
    for county in counties:
        try:
            c.execute("""SELECT id FROM states WHERE name = %s""", (county[1],))
            state_id = c.fetchone()

            if state_id is None:
                continue

            c.execute("""SELECT id FROM counties WHERE name = %s AND state_id = %s""", (county[0], state_id[0],))
            county_id = c.fetchone()

            if county_id is not None:
                continue

            c.execute("""INSERT INTO counties(name, fips, state_id)
            VALUES (%s, %s, %s)""", (county[0], county[2], state_id[0],))
        except Exception as e:
            print(e)
            sys.exit(2)

    c.close()
    db.commit()

def transform_us_data(db):
    print('Transforming US data')

    c = db.cursor()

    c.execute("""SELECT date, cases, deaths FROM ny_times_us ORDER BY date""")
    nytimes = c.fetchall()

    c.execute("""TRUNCATE TABLE us_data""")
    data = []

    seven_days = [0,0,0,0,0,0,0]
    prev_cases = 0

    for record in nytimes: 
        new_cases = record[1] - prev_cases
        prev_cases = record[1]

        seven_days.pop(0)
        seven_days.append(new_cases)

        data.append((record[0], record[1], record[2], new_cases, statistics.mean(seven_days)))
    
    try: 
        c.executemany("""INSERT INTO us_data (date, cases, deaths, new_cases, seven_day_average_cases)
        VALUES (%s, %s, %s, %s, %s)""", data)
    except Exception as e:
        print(e)
        sys.exit(2)

    c.close()
    db.commit()




def transform_state_data(db):
    print('Transforming state data')

    c = db.cursor()

    c.execute("""SELECT id, name, fips FROM states ORDER BY name""")
    states = c.fetchall()

    c.execute("""TRUNCATE TABLE state_data""")

    for state in states:
        c.execute("""SELECT date, cases, deaths FROM ny_times_us_states WHERE state = %s ORDER BY date""", (state[1],))
        nytimes = c.fetchall()

        seven_days = [0,0,0,0,0,0,0]
        prev_cases = 0

        data = []

        for record in nytimes:
            new_cases = record[1] - prev_cases
            prev_cases = record[1]

            seven_days.pop(0)
            seven_days.append(new_cases)

            data.append((record[0], record[1], record[2], state[0], new_cases, statistics.mean(seven_days)))

        try: 
            c.executemany("""INSERT INTO state_data (date, cases, deaths, state_id, new_cases, seven_day_average_cases)
            VALUES (%s, %s, %s, %s, %s, %s)""", data)
        except Exception as e:
            print(e)
            sys.exit(2)

    c.close()
    db.commit()



def transform_county_data(db):
    print('Transforming county data')

    c = db.cursor()

    c.execute("""SELECT c.id, c.name, c.fips, c.state_id, s.name FROM counties AS c
    INNER JOIN states AS s ON c.state_id = s.id 
    ORDER BY c.name""")
    counties = c.fetchall()

    c.execute("""TRUNCATE TABLE county_data""")

    for county in counties:
        c.execute("""SELECT date, cases, deaths FROM ny_times_us_counties 
        WHERE state = %s AND county = %s 
        ORDER BY date""", (county[4], county[1]))
        nytimes = c.fetchall()

        seven_days = [0,0,0,0,0,0,0]
        prev_cases = 0

        data = []

        for record in nytimes:
            new_cases = record[1] - prev_cases
            prev_cases = record[1]

            seven_days.pop(0)
            seven_days.append(new_cases)

            data.append((record[0], record[1], record[2], county[0], new_cases, statistics.mean(seven_days)))

        try: 
            c.executemany("""INSERT INTO county_data (date, cases, deaths, county_id, new_cases, seven_day_average_cases)
            VALUES (%s, %s, %s, %s, %s, %s)""", data)
        except Exception as e:
            print(e)
            sys.exit(2)

    c.close()
    db.commit()
    


def transform(db):
    print('Transforming…')

    get_states_from_nytimes_data(db)
    get_counties_from_nytimes_data(db)
    transform_us_data(db)
    transform_state_data(db)
    transform_county_data(db)


    

parser = argparse.ArgumentParser(description="NY Times Data ETL")
parser.add_argument('-p', help='database password', dest="db_password", required=True)
parser.add_argument('--host', help='database host', dest="db_host", required=True)
parser.add_argument('-u', help='database user', dest="db_user", required=True)
parser.add_argument('-n', help='database name', dest="db_name", required=True)
args = parser.parse_args()

db=MySQLdb.connect(passwd=args.db_password, host=args.db_host, user=args.db_user, db=args.db_name)

extract(db)
transform(db)

sys.exit()