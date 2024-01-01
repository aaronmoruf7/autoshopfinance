from functools import wraps
from flask import session, redirect
from .models import db, Transaction 
from sqlalchemy import  cast, func, Date, extract
from datetime import datetime


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def calculate_financial_summary(username):
    # Get the current year
    current_year = datetime.now().year

    # Calculate total income
    total_income_query = (
        db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0).label('total')
        )
        .filter(Transaction.type == 'income')
        .filter(Transaction.username == username)
        .filter(extract('year', cast(Transaction.date, Date)) == current_year)
    )
    total_income = total_income_query.scalar()

    # Calculate total expenses
    total_expense_query = (
        db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
            )
        .filter(Transaction.type == 'expense')
        .filter(Transaction.username == username)
        .filter(extract('year', cast(Transaction.date, Date)) == current_year)
    )
    total_expenses = total_expense_query.scalar()
    

    # Calculate net profit
    net_profit = total_income - total_expenses

    return total_income, total_expenses, net_profit


def calculate_total_cost(parts_items, labour_items, other_items):
    total_cost = 0.0

    for items in [parts_items, labour_items, other_items]:
        for _, cost in items:
            total_cost += float(cost)

    return total_cost


def usd(value):
    """Format value as USD."""
    return f"{value:,.2f}"


def format_number_with_commas(value):
    return "{:,.2f}".format(float(value))


def format_number_with_commas_no_decimal(value):
    return "{:,.0f}".format(float(value))


def init_app(app):
    db.init_app(app)
