
from flask import (flash, redirect, render_template, request, session, make_response, Blueprint)
from werkzeug.security import check_password_hash, generate_password_hash
from .forms import (LoginForm, RegistrationForm, ChangePasswordForm, IncomeForm, ExpenseForm, CustomerForm,)
import pdfkit
from sqlalchemy import func, case, DateTime, cast
from .helpers import (
    login_required,
    calculate_financial_summary,
)
from .models import db, User, Transaction, Customer  

app = Blueprint('app', __name__)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Registration Page
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm(request.form)

    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data
        confirm_password = form.confirm_password.data

        # Check if the username already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already taken. Please choose another.", "error")
            return redirect("/register")

        # Check if password and confirmation match
        if password != confirm_password:
            flash("Password and confirmation do not match.", "error")
            return redirect("/register")

        # Hash the password before storing it in the database
        hashed_password = generate_password_hash(password)

        # Add user to the database

        # Create a new User instance
        new_user = User(username=username, hash=hashed_password)

        # Add the new user to the database
        db.session.add(new_user)

        # Commit the changes to the database
        db.session.commit()

        # Log the user in
        session["user_id"] = username

        flash("Registration successful!", "success")
        return redirect("/")

    return render_template("register.html", form=form, active_page="register")


# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)

    # Forget any user_id
    session.clear()

    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user is None or not check_password_hash(user.hash, password):
            flash("Invalid username or password. Please try again.", "error")
            return redirect("/login")

        session["user_id"] = user.username
        flash("Login successful!", "success")
        return redirect("/")

    return render_template("login.html", form=form, active_page="login")


# Change Password Page
@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change user password"""

    form = ChangePasswordForm(request.form)

    # Get username of the current user
    username = session.get("user_id")

    # User reached route via POST
    if request.method == "POST":
        # Ensure old password was submitted
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")

        if not old_password or not new_password or not confirmation:
            flash("Please fill in all fields.", "error")
            return redirect("/change_password")

        # Make sure old_password was entered correctly
        rows = User.query.filter_by(username=username).value('hash')

        if not check_password_hash(rows[0], old_password):
            flash("Incorrect old password. Please try again.", "error")
            return redirect("/change_password")

        # Generate a hash of the new password
        hashed_password = generate_password_hash(new_password)

        # Update the user's password in the database
        user = User.query.filter_by(username=username).first()
        # Update the hashed password
        user.hash = hashed_password

        # Commit the changes to the database
        db.session.commit()

        # Flash a success message
        flash("Password changed successfully!", "success")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET
    else:
        return render_template(
            "change_password.html", form=form, active_page="change_password"
        )


# Logout
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


# Home Page
@app.route("/")
@login_required
def home():
    username = session.get("user_id")

    # Calculate financial summary
    total_income, total_expenses, net_profit = calculate_financial_summary(username)

    # Fetch recent transactions from the database
    recent_transactions = (
        Transaction.query.filter_by(username=username)
        .order_by(Transaction.date.desc())
        .limit(10)
        .all()
    )

    # Fetch monthly net profit/loss data from the database

    monthly_data = (
        db.session.query(
            # func.date_trunc('month', cast(Transaction.date, DateTime)).label('month'),
            func.to_char(func.date_trunc('month', cast(Transaction.date, DateTime)), 'Mon YYYY').label('month'),
            func.sum(
                case(
                    (Transaction.type == 'income', Transaction.amount),
                    else_=-Transaction.amount
                )
            ).label('net_profit')
        )
        .filter_by(username=username)
        .group_by(func.date_trunc('month', cast(Transaction.date, DateTime)))
        .all()
    )

    # Extract labels and values for the chart
    chart_labels = [entry[0] for entry in monthly_data]  # Assuming 'month' is the first label
    chart_values = [entry[1] for entry in monthly_data]  # Assuming 'net_profit' is the second label

    net_profit_is_negative = net_profit < 0

    return render_template(
        "home.html",
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=net_profit,
        recent_transactions=recent_transactions,
        chart_labels=chart_labels,
        chart_values=chart_values,
        net_profit_is_negative=net_profit_is_negative,
        active_page="home",
    )


# Income Page
@app.route("/income")
@login_required
def income():
    username = session.get("user_id")

    # Retrieve income transactions from the database
    transactions = Transaction.query.filter_by(type='income', username=username).all()
    return render_template(
        "income.html", transactions=transactions, active_page="income"
    )


# Add Income Page
@app.route("/add_income", methods=["GET", "POST"])
@login_required
def add_income():
    form = IncomeForm()

    username = session.get("user_id")

    if request.method == "POST":
        # Get form data
        description = request.form.get("description")
        amount = request.form.get("amount")
        date = request.form.get("date")

        # Validate form data
        if not description or not amount or not date:
            flash("Please fill in all fields.", "error")
            return redirect("add_income")

        # Insert income transaction into the database
        new_transaction = Transaction(username=username, type='income', description=description, amount=amount, date=date)
        db.session.add(new_transaction)
        db.session.commit()

        flash("Income transaction added successfully!", "success")
        return redirect("/income")

    return render_template("add_income.html", form=form, active_page="income")


# Delete Income
@app.route("/delete_income", methods=["POST"])
@login_required
def delete_income():
    username = session.get("user_id")

    # Get the transaction_id from the form submission
    transaction_id = request.form.get("transaction_id")

    # Query the database to get the income transaction by ID using Flask-SQLAlchemy
    income_transaction = Transaction.query.filter_by(id=transaction_id, type='income', username=username).first()

    # Check if the result is not empty
    if income_transaction:
        # Delete the transaction from the database using Flask-SQLAlchemy
        db.session.delete(income_transaction)
        db.session.commit()

        flash("Income transaction deleted successfully!", "success")
    else:
        flash("Invalid transaction or permission denied.", "error")


    # Redirect back to the income page
    return redirect("/income")


# Expense Page
@app.route("/expense")
@login_required
def expense():
    username = session.get("user_id")

    # Retrieve expense transactions from the database
    transactions = Transaction.query.filter_by(type='expense', username=username).all()
    return render_template(
        "expense.html", transactions=transactions, active_page="expense"
    )


# Add Expense Page
@app.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    form = ExpenseForm()

    username = session.get("user_id")

    if request.method == "POST":
        # Get form data
        description = request.form.get("description")
        amount = request.form.get("amount")
        date = request.form.get("date")

        # Validate form data
        if not description or not amount or not date:
            flash("Please fill in all fields.", "error")
            return redirect("/add_expense")

        # Insert expense transaction into the database using Flask-SQLAlchemy
        new_transaction = Transaction(username=username, type='expense', description=description, amount=amount, date=date)
        db.session.add(new_transaction)
        db.session.commit()

        flash("Expense transaction added successfully!", "success")
        return redirect("/expense")

    return render_template("add_expense.html", form=form, active_page="expense")


# Delete Expense
@app.route("/delete_expense", methods=["POST"])
@login_required
def delete_expense():
    username = session.get("user_id")

    # Get the transaction_id from the form submission
    transaction_id = request.form.get("transaction_id")

    # Query the database to get the expense transaction by ID using Flask-SQLAlchemy
    expense_transaction = Transaction.query.filter_by(id=transaction_id, type='expense', username=username).first()

    # Check if the result is not empty
    if expense_transaction:
        # Delete the transaction from the database using Flask-SQLAlchemy
        db.session.delete(expense_transaction)
        db.session.commit()

        flash("Expense transaction deleted successfully!", "success")
    else:
        flash("Invalid transaction or permission denied.", "error")


    # Redirect back to the expense page
    return redirect("/expense")


# Receipt Generation
@app.route("/generate_receipt", methods=["GET", "POST"])
@login_required
def generate_receipt():
    if request.method == "POST":
        # Retrieve data from the form
        invoice_number = request.form.get("invoice_number")
        customer_name = request.form.get("customer_name")
        customer_email = request.form.get("customer_email")
        customer_address = request.form.get("customer_address")
        customer_phone = request.form.get("customer_phone")
        customer_vehicle = request.form.get("customer_vehicle")
        vehicle_license_plate = request.form.get("vehicle_license_plate")
        vehicle_mileage = request.form.get("vehicle_mileage")
        receipt_date = request.form.get("receipt_date")

        # Retrieve data for Parts, Labour, Other sections
        parts_items = request.form.getlist("part_description[]")
        parts_costs = request.form.getlist("part_cost[]")
        labour_items = request.form.getlist("labour_description[]")
        labour_costs = request.form.getlist("labour_cost[]")
        other_items = request.form.getlist("other_description[]")
        other_costs = request.form.getlist("other_cost[]")
        # Retrieve data for discount
        discount_input = request.form.get(
            "discount", ""
        )  # Get the input or an empty string if not provided
        discount = (
            float(discount_input) if discount_input else 0
        )  # Convert to float or use 0 if empty

        # Calculate total cost
        total_cost = sum(
            [float(cost) for cost in parts_costs + labour_costs + other_costs]
        )
        discount_value = total_cost * (discount / 100)

        # Generate HTML for receipt
        receipt_template = render_template(
            "receipt_template.html",
            invoice_number=invoice_number,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_address=customer_address,
            customer_phone=customer_phone,
            customer_vehicle=customer_vehicle,
            vehicle_license_plate=vehicle_license_plate,
            vehicle_mileage=vehicle_mileage,
            receipt_date=receipt_date,
            parts_items=zip(parts_items, parts_costs),
            labour_items=zip(labour_items, labour_costs),
            other_items=zip(other_items, other_costs),
            discount=discount,
            discount_value=discount_value,
            total_cost=total_cost,
        )

        pdf = pdfkit.from_string(receipt_template, False)

        # Serve PDF as a response
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = "inline; filename=receipt.pdf"
        return response

    # If not a POST request, render the form
    return render_template("generate_receipt.html", active_page="generate_receipt")


# Customer Database
@app.route("/customers")
@login_required
def customers():
    username = session.get("user_id")
    customers_data = Customer.query.filter_by(username=username).all()
    return render_template(
        "customers.html", customers=customers_data, active_page="customers"
    )


# Add Customer
@app.route("/add_customer", methods=["GET", "POST"])
@login_required
def add_customer():
    form = CustomerForm()

    username = session.get("user_id")

    if request.method == "POST" and form.validate():
        # Extract data from the form
        name = form.name.data
        number = form.number.data
        email = form.email.data
        address = form.address.data

        # Create a new Customer instance
        new_customer = Customer(
            username=username,
            name=name,
            number=number,
            email=email,
            address=address
        )

        # Add the new customer to the database
        db.session.add(new_customer)
        db.session.commit()

        flash("Customer added successfully!", "success")
        return redirect("/customers")

    return render_template("add_customer.html", form=form, active_page="customers")


# Delete Customer
@app.route("/delete_customer", methods=["POST"])
@login_required
def delete_customer():
    username = session.get("user_id")

    # Get the customer_id from the form submission
    customer_id = request.form.get("customer_id")

    # Query the database to get the customer by ID
    customer = Customer.query.filter_by(id=customer_id).first()

    # Check if the result is not empty
    if customer:
        # Check if the customer belongs to the current user
        if customer.username == username:
            # Delete the customer from the database
            db.session.delete(customer)
            db.session.commit()
            flash("Customer deleted successfully!", "success")
        else:
            flash("Invalid customer or permission denied.", "error")
    else:
        flash("Customer not found.", "error")


    # Redirect back to the income page
    return redirect("/customers")