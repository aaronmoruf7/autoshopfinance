from flask import Flask
from models import db
import os

# Configure application
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config['SECRET_KEY'] = '1234567'
#export DATABASE_URL=postgresql://autoshopfinance_user:3vRhG78iSkEti5zAUgtnyU8A8ahLs00K@dpg-cm7gl4nqd2ns73f3ordg-a.ohio-postgres.render.com/autoshopfinance

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)  # Initialize SQLAlchemy with the Flask app
