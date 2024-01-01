import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from .models import db

def create_app():
    # Configure application
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config['SECRET_KEY'] = '1234567'
    #export DATABASE_URL=postgresql://autoshopfinance_user:3vRhG78iSkEti5zAUgtnyU8A8ahLs00K@dpg-cm7gl4nqd2ns73f3ordg-a.ohio-postgres.render.com/autoshopfinance
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # db = SQLAlchemy(app)
    db.init_app(app)

    migrate = Migrate(app, db)
    Session(app)

    from .routes import app as app_blueprint
    from .helpers import (usd, format_number_with_commas, format_number_with_commas_no_decimal)

    app.jinja_env.filters["formatNumberWithCommas"] = format_number_with_commas
    app.jinja_env.filters["formatNumberWithCommasNoDecimal"] = format_number_with_commas_no_decimal
    app.jinja_env.filters["usd"] = usd

    app.register_blueprint(app_blueprint)

    return app


