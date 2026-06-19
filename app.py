import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from flask_session import Session
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    try:
        rows = db.execute(
            "SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING shares > 0;",
            session["user_id"],
        )
        holdings = []
        allocated_stock_value = 0
        for row in rows:
            stock_data = lookup(row["symbol"])
            total_value = row["shares"] * stock_data["price"]
            allocated_stock_value += total_value
            holdings.append(
                {
                    "symbol": row["symbol"],
                    "name": stock_data["name"],
                    "shares": row["shares"],
                    "price": stock_data["price"],
                    "total": total_value,
                },
            )
        user_data = db.execute(
            "SELECT username, cash FROM users WHERE id = ?;", session["user_id"]
        )[0]
        return render_template(
            "index.html",
            holdings=holdings,
            username=user_data["username"],
            cash=user_data["cash"],
            grand_total=user_data["cash"] + allocated_stock_value,
        )
    except:
        return apology("Something went wrong")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        try:
            symbol = request.form.get("symbol").upper()
            shares = int(request.form.get("shares"))
            if not symbol:
                return apology("Provide symbol")
            if int(shares) < 1:
                return apology("Shares must be positive number")
            stock_data = lookup(symbol)
            if stock_data == None:
                return apology("Wrong symbol")
            cash = db.execute(
                "SELECT cash FROM users WHERE id= ?;", session["user_id"]
            )[0]["cash"]
            if int(cash) < int(stock_data["price"]) * int(shares):
                return apology("You don't have enough cash")
            # implenment the purchase
            db.execute(
                "UPDATE users SET cash = ? WHERE id= ?;",
                cash - (stock_data["price"] * shares),
                session["user_id"],
            )
            db.execute(
                "INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?);",
                session["user_id"],
                stock_data["symbol"],
                shares,
                stock_data["price"],
                "BUY",
            )
            flash(f"Successfully bought {shares} share(s) of {stock_data['symbol']}!")
            return redirect("/")
        except:
            return apology("Something went wrong")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute(
        "SELECT symbol, shares, price, type, timestamp FROM transactions WHERE user_id = ?",
        session["user_id"],
    )
    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        stock_symbol = request.form.get("query")
        if not stock_symbol:
            return apology("Must provide stock symbol")
        stock = lookup(stock_symbol)
        if stock == None:
            return apology("Stock symbol is wrong")
        return render_template("quoted.html", stock=stock)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("Must provide Username")
        if not request.form.get("password"):
            return apology("Must provide Password / Confirm Password")
        if not request.form.get("password") == request.form.get("confirmPassword"):
            return apology("Passwords do not match")
        try:
            hash = generate_password_hash(request.form.get("password"))
            db.execute(
                "INSERT INTO users (username, hash) VALUES(?, ?)",
                request.form.get("username"),
                hash,
            )
            flash("Registration successful! Please log in.")
            return redirect("/login")
        except ValueError:
            return apology("Username already used")
        except:
            return apology("Something went wrong!")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        try:
            symbol = request.form.get("symbol")
            shares = int(request.form.get("shares"))
            stock_data = lookup(symbol)
            if stock_data == None:
                return apology("Wrong symbol")
            if shares < 1:
                return apology("Shares must be positive number")
            row = db.execute(
                "SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? AND symbol=? GROUP BY symbol HAVING shares > 0;",
                session["user_id"],
                symbol,
            )[0]
            if row["shares"] < shares:
                return apology("you don't not own that many shares of the stock")
            # implenment sell
            cash = db.execute("SELECT cash FROM users WHERE id= ?", session["user_id"])[
                0
            ]["cash"]
            db.execute(
                "INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?);",
                session["user_id"],
                stock_data["symbol"],
                -shares,
                stock_data["price"],
                "SELL",
            )
            db.execute(
                "UPDATE users SET cash = ? WHERE id= ?;",
                cash + (stock_data["price"] * shares),
                session["user_id"],
            )
            flash(f"Successfully sold {shares} share(s) of {stock_data['symbol']}!")
            return redirect("/")
        except:
            return apology("Something went wrong")
    else:
        holdings = []
        rows = db.execute(
            "SELECT symbol, SUM(shares) AS shares FROM transactions WHERE user_id = ? GROUP BY symbol HAVING shares > 0;",
            session["user_id"],
        )
        for row in rows:
            holdings.append({"symbol": row["symbol"], "shares": row["shares"]})
        return render_template("sell.html", holdings=holdings)


@app.route("/account")
@login_required
def settings():
    return render_template("account.html")


@app.route("/change_username", methods=["POST"])
@login_required
def change_username():
    new_username = request.form.get("new_username")
    if not new_username:
        return apology("invalid new username")
    rows = db.execute("SELECT username FROM users WHERE username = ?;", new_username)
    # check if username exsist
    if len(rows) != 0:
        return apology("Username already exsist")
    try:
        user_data = db.execute("SELECT * FROM users WHERE id= ?;", session["user_id"])[
            0
        ]
        # check password is correct
        if not check_password_hash(user_data["hash"], request.form.get("password")):
            return apology("Wrong password")
        db.execute(
            "UPDATE users SET username = ? WHERE id =?;",
            new_username,
            session["user_id"],
        )
        flash("Username updated successfully!")
        return redirect("/")
    except:
        return apology("Something went wrong")


@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    new_password = request.form.get("new_password")
    if not new_password == request.form.get("confirmation"):
        return apology("passwords don't match")
    try:
        user_data = db.execute("SELECT * FROM users WHERE id= ?;", session["user_id"])[
            0
        ]
        if not check_password_hash(
            user_data["hash"], request.form.get("current_password")
        ):
            return apology("Wrong password")
        if check_password_hash(user_data["hash"], new_password):
            return apology("you used this password before")
        new_hash = generate_password_hash(new_password)
        db.execute(
            "UPDATE users SET hash = ? WHERE id =?;", new_hash, session["user_id"]
        )
        flash("Password updated successfully! Please log in again.")
        return redirect("/logout")
    except:
        return apology("Something went wrong")


@app.route("/add_cash", methods=["GET", "POST"])
@login_required
def add_cash():
    """Allow user to add additional cash to their account"""
    if request.method == "POST":
        amount_input = request.form.get("amount")

        # 1. Validate that an amount was submitted
        if not amount_input:
            return apology("must provide an amount", 400)

        # 2. Ensure the input is a valid positive number
        try:
            amount = float(amount_input)
            if amount <= 0:
                return apology("amount must be a positive number", 400)
        except ValueError:
            return apology("amount must be a valid number", 400)

        # 3. Update user's cash balance in the database
        db.execute(
            "UPDATE users SET cash = cash + ? WHERE id = ?;", amount, session["user_id"]
        )

        # 4. Flash a success message and redirect to homepage
        flash(f"Successfully added {usd(amount)} to your account balance!")
        return redirect("/")

    else:
        return render_template("add_cash.html")
