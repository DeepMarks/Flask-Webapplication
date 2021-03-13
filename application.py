import os
import os.path
from os import path
import camelot
import csv
import requests

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# configure application
app = Flask(__name__)

# ensuring templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# ensuring responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure lib to use slqite3 database
db = SQL("sqlite:///sports.db")

# configure web application routes
@app.route("/")
@login_required
def index():
    "show sports homepage"

    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])

    return render_template("index.html", dbase=dbase)

@app.route("/analytics")
@login_required
def analytics():
    "show player analytics"

    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    user = dbase[0]["id"]
    name = dbase[0]["name"]

    pbase = db.execute("SELECT * FROM players")

    if len(pbase) == 0:
        # read csv into database
        with open("ranking.csv", "r") as ranking:
            reader = csv.DictReader(ranking, delimiter=",")

            for row in reader:

                players = []

                players.append(row["Rackets"])
                players.append(row["Rank"])
                players.append(row["Name"])
                players.append(row["Prev"])
                players.append(row["ID"])
                players.append(row["Points"])

                db.execute("INSERT INTO players (Rackets, Rank, Name, Surname, ID, Points) VALUES(?, ?, ?, ?, ?, ?)", players[0], players[1], players[2], players[3], players[4], players[5])

    db_player = db.execute("SELECT * FROM history WHERE user_id = :id", id = user)
    if len(db_player) == 0:
        month = 0
        for i in range(12):
            month += 1
            if path.exists("ranking" + str(month) + ".csv") == True:
                with open("ranking" + str(month) + ".csv", "r") as ranking:
                    reader = csv.DictReader(ranking, delimiter=",")

                    for row in reader:

                        if row["Name"] == name:
                            history = []

                            history.append(row["Rackets"])
                            history.append(row["Rank"])
                            history.append(row["Name"])
                            history.append(row["ID"])
                            history.append(row["Points"])

                            db.execute("INSERT INTO history (user_id, month, rackets, rank, name, player_id, points) VALUES(?, ?, ?, ?, ?, ?, ?)", user, month, history[0], history[1], history[2], history[3], history[4])
                            db_player = db.execute("SELECT * FROM history WHERE user_id = :id", id = user)
            else:
                print(path.exists("ranking" + str(month) + ".csv"))

    year = []
    month = []
    rank = []
    for i in range(len(db_player)):
        y = 2020
        m = db_player[i]["month"]
        year.append(y)
        month.append(m)
        rank.append(db_player[i]["rank"])
        m += 1

    return render_template("analytics.html", dbase=dbase, pbase=pbase, year=year, month=month, rank=rank)

@app.route("/tour")
@login_required
def tour():
    "show info about tour"

    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])


    return render_template("tour.html", dbase=dbase)

@app.route("/history")
@login_required
def history():
    "show info about history"

    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])

    return render_template("history.html", dbase=dbase)

@app.route("/about")
@login_required
def about():
    "show info about team"

    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])

    return render_template("about.html", dbase=dbase)


@app.route("/profile")
@login_required
def profile():
    """Show user profile and options"""

    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])

    # player rating
    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    name = dbase[0]["name"]
    player = db.execute("SELECT * FROM players WHERE Name = :name", name = name)

    return render_template("profile.html", dbase=dbase, player=player)


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change password"""
    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])

    # User reached route via GET
    if request.method == "GET":
        return render_template("password.html", dbase=dbase)
    # User reached route via POST (as by submitting a form via POST)
    else:

        # Ensure old password was submitted
        if not request.form.get("old"):
            return apology("must provide old password", 403)

        # Ensure new password was submitted
        if not request.form.get("new"):
            return apology("must provide new password", 403)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 403)

        # Ensure passwords match
        elif request.form.get("new") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        # Check user database for password hash
        user_db = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
        for i in range(len(user_db)):
            pw_hash = user_db[i]["hash"]

        old = request.form.get("old")
        new = request.form.get("new")
        new_hash = generate_password_hash(request.form.get("new"))

        # Ensure username exists and password is correct
        if not check_password_hash(pw_hash, old):
            return apology("old password is incorrect", 403)

        # ensure new password is not the same as old password
        elif old == new:
            return apology("new password is same as old", 403)

        else:
            # Update the password for this user
            db.execute("UPDATE users SET hash = :hash WHERE id = :id", hash = new_hash, id = session["user_id"])

        # Redirect user back to profile
        return redirect("/profile")

@app.route("/success")
@login_required
def success():
    """Successful dark/light mode"""

    dbase = db.execute("SELECT * FROM users WHERE id = :id", id=session["user_id"])
    dmode = dbase[0]["mode"]

    if dmode == 1:
        # Update the mode for this user
        db.execute("UPDATE users SET mode = :mode WHERE id = :id", mode = 0, id = session["user_id"])
        dmode = 0
    else:
        # Update the mode for this user
        db.execute("UPDATE users SET mode = :mode WHERE id = :id", mode = 1, id = session["user_id"])
        dmode = 1

    return render_template("success.html", dbase=dbase)



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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via GET
    if request.method == "GET":
        return render_template("register.html")

    # User reached route via POST (as by submitting a form via POST)
    else:

        # Ensure username was submitted
        if not request.form.get("first"):
            return apology("must provide first name", 403)

        # Ensure username was submitted
        if not request.form.get("last"):
            return apology("must provide last name", 403)

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password", 403)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 403)

        hash = generate_password_hash(request.form.get("password"))

        # Check user database for username
        user_db = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if len(user_db) == 1:

            username = user_db[0]["username"]

            # Ensure the username is not in the database already
            if request.form.get("username") == username:
                return apology("username is already registered", 403)

        else:
            # Add new user to database if not existing yet
            name = request.form.get("last") + "\n" + request.form.get("first")
            mode = 1
            user = db.execute("INSERT INTO users (username, hash, name, mode) VALUES (:username, :hash, :name, :mode)", username=request.form.get("username"), hash=hash, name=name, mode=mode)

        # remember which user has logged in
        session["user_id"] = user


        # Redirect user to home page
        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)