import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .db import get_db

db = get_db()

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_pyfile('settings.py')

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)

    with app.app_context():
        from . import covid
        app.register_blueprint(covid.bp)
        app.add_url_rule('/', endpoint='index')

        @app.template_filter()
        def svg_points(data, max_x, max_y, viewport_x, viewport_y, init_x=0):
            points = []

            for index, datum in enumerate(data):
                points.append("{},{}".format((index + init_x) * viewport_x / max_x, viewport_y - (datum.seven_day_average_cases / max_y * viewport_y)))

            return " ".join(points)

        return app

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app