"""This is the python file that runs the flask app for athletics records. It creates all the routes and functions to display and change records in the database."""

import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "Cabbage tree"

DATABASE = "athletics.db"
#User name for login is admin and password is Cabbage tree

def login_required(f):
    """ Ensures that the user is logged in before they can access certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def get_db():
    """This returns the database connection for the current request."""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(_exception):
    """Close the database connection after each request."""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    """Looks at the username and password to cheak if they are correct and if they are it will log them in, if not they get an error message."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, password FROM admin_users WHERE username = ?", (username,)
        )
        user = cur.fetchone()
        # Compares the username and hashed password to what the user entered and if they match then the user will be logged in for the session.
        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = username
            return redirect(url_for("home"))
        flash("Invalid login", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    """This logs the user out and redirect them to the home page by clearing the session."""
    session.clear()
    return redirect("/")


@app.route("/admin")
@login_required
def admin_panel():
    """Cheaks if the user is logged in before they can access the admin panel."""
    return render_template("admin.html")


@app.route("/admin/manage", methods=["GET", "POST"])
@login_required
def manage_database():
    """This creates a page with all records from the database that the user can chooose to edit."""
    conn = get_db()
    cur = conn.cursor()

    # etches all records from the database and joins them.
    cur.execute("""
        SELECT records.id, records.year, event.name, age_group.name,
        person.name, records.bhs_record
        FROM records
        INNER JOIN event ON records.event_id = event.id
        INNER JOIN age_group ON records.age_group_id = age_group.id
        INNER JOIN person ON records.person_id = person.id
    """)
    records = cur.fetchall()

    #Get events and age groups that were selected in the admin panel.
    cur.execute("SELECT id, name FROM event ORDER BY name")
    events = cur.fetchall()
    cur.execute("SELECT id, name FROM age_group ORDER BY name")
    age_groups = cur.fetchall()
    cur.execute("SELECT id, name FROM person ORDER BY name")
    people = cur.fetchall()

    #Loops through the records and displays editable rows of data for each record.
    return render_template(
        "manage.html",
        records=records,
        events=events,
        age_groups=age_groups,
        people=people,
    )


#Update existing record
@app.route("/admin/update_record/<int:record_id>", methods=["POST"])
@login_required
def update_record(record_id):
    """ This takes the submitted changes and updates an existing record in the database. The only categories it does not allow to be changed are the event and age group. """
    year = request.form.get("year")
    person_name = request.form.get("person_name")
    bhs_record = request.form.get("bhs_record")

    #This section is to validate inputs the user gives.
    if not year or not person_name or not bhs_record:
        flash("All fields are required", "error")
        return redirect(url_for("manage_database"))

    try:
        year = int(year)
    except ValueError:
        flash("Year must be a number!", "error")
        return redirect(url_for("manage_database"))

    if int(year) < 1900 or int(year) > 2026:
        flash("Must be between 1900 and 2026!", "error")
        return redirect(url_for("manage_database"))

    try:
        bhs_record = float(bhs_record) and bhs_record < 0
    except ValueError:
        flash("Record must be a number!", "error")
        return redirect(url_for("manage_database"))

    if bhs_record < 0:
        flash("Record must be a positive number!", "error")
        return redirect(url_for("manage_database"))

    conn = get_db()
    cur = conn.cursor()

    #Get the current person ID from the record
    cur.execute("SELECT person_id FROM records WHERE id = ?", (record_id,))
    result = cur.fetchone()

    #If for some reason the record does not exist, flash an error message and redirect to the manage database page.
    if not result:
        flash("Record not found!", "error")
        return redirect(url_for("manage_database"))

    #Gets the person's ID from the result
    person_id = result[0]

    #Update the person's name and uses the same person's ID
    cur.execute("UPDATE person SET name = ? WHERE id = ?", (person_name, person_id))

    #Updates the record table changing the year and burnside record.
    cur.execute(
        """
        UPDATE records
        SET year = ?, bhs_record = ?
        WHERE id = ?
    """,
        (year, bhs_record, record_id),
    )

    #Check to see if the update was successful and gives an error if it was not.
    if cur.rowcount == 0:
        flash("Failed to update record!", "error")
    else:
        flash("Record updated successfully!", "success")

    conn.commit()

    return redirect(url_for("manage_database"))


def query_db(query, args=(), one=False):
    """This function executes a query on the database and returns the results."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route("/")
def home():
    """This is the home route which displays the form that allows you to filter the records."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT records.id, records.year, event.name, age_group.name,
        person.name, records.bhs_record
        FROM records
        INNER JOIN event ON records.event_id = event.id
        INNER JOIN age_group ON records.age_group_id = age_group.id
        INNER JOIN person ON records.person_id = person.id
    """)
    records = cur.fetchall()
    events = query_db("SELECT id, name FROM event;")
    age_groups = query_db("SELECT id, name FROM age_group;")
    return render_template(
        "home.html", records=records, events=events, age_groups=age_groups
    )


@app.route("/records")
def records_table():
    """ This route get's all records in the database and displays them """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
                SELECT records.id, records.year, event.name, age_group.name,
                person.name, records.bhs_record
                FROM records
                INNER JOIN event ON records.event_id = event.id
                INNER JOIN age_group ON records.age_group_id = age_group.id
                INNER JOIN person ON records.person_id = person.id
                """)
    record = cur.fetchall()
    return render_template("records.html", record=record)


@app.route("/submit", methods=["POST"])
def submit():
    """ This is the route for the submission form on the home page that filters the records based on the selected event and age group. """
    selected_event = request.form.get("events")
    selected_age_group = request.form.get("age_groups")
    conn = get_db()
    cur = conn.cursor()
    #This is in case both are set to defult. Does the same thing as the all records route.
    if selected_event == "All events" and selected_age_group == "All years":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
        """,
        )
    #This is for if they select all boys records from a all events.
    elif selected_age_group == "Boys" and selected_event == "All events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE age_group.Gender = 2
        """,
        )
    #This is for if they select all girls records from a all events.
    elif selected_age_group == "Girls" and selected_event == "All events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE age_group.Gender = 1
        """,
        )
    #This is for if they select all track event records from all year groups.
    elif selected_age_group == "All years" and selected_event == "All track events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE event.Event_type = 1
            ORDER BY event.id ASC
        """,
        )
    #This is for if they select all field event records from all year groups.
    elif selected_age_group == "All years" and selected_event == "All field events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE event.Event_type = 2
            ORDER BY event.id ASC
        """,
        )
    #This is for if they select all boys records from all field events.
    elif selected_age_group == "Boys" and selected_event == "All field events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE event.Event_type = 2 and age_group.Gender = 2
        """,
        )
    #This is for if they select all boys records from all track events.
    elif selected_age_group == "Boys" and selected_event == "All track events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE event.Event_type = 1 and age_group.Gender = 2
        """,
        )
    #This is for if they select all girls records from all field events.
    elif selected_age_group == "Girls" and selected_event == "All field events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE event.Event_type = 2 and age_group.Gender = 1
        """,
        )
    #This is for if they select all girls records from all track events.
    elif selected_age_group == "Girls" and selected_event == "All track events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE event.Event_type = 1 and age_group.Gender = 1
        """,
        )
    #This is for if they select all boys records from a specific event.
    elif selected_age_group == "Boys":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE age_group.Gender = 2 AND records.event_id = ?
        """,
            (selected_event,),
        )
    #This is for if they select all girls records from a specific event.
    elif selected_age_group == "Girls":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE age_group.Gender = 1 AND records.event_id = ?
        """,
            (selected_event,),
        )
    #This is for if they select all track records from a specific age group.
    elif selected_event == "All track events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE records.age_group_id = ? AND event.Event_type = 1
        """,
            (selected_age_group,),
        )
    #This is for if they select all field records from a specific age group.
    elif selected_event == "All field events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE records.age_group_id = ? AND event.Event_type = 2
        """,
            (selected_age_group,),
        )
    #This is for if they select all events and one age group. It will show all
    #Events records for that age group.
    elif selected_event == "All events":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE records.age_group_id = ?
        """,
            (selected_age_group,),
        )
    #This is for if they select all age groups and one event. It will show all age group records for that one specific event.
    elif selected_age_group == "All years":
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE records.event_id = ?
        """,
            (selected_event,),
        )
    #This is for if they want a specific record for that age group and event.
    else:
        cur.execute(
            """
            SELECT records.id, records.year, event.name, age_group.name,
            person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE records.age_group_id = ? AND records.event_id = ?
            ORDER BY records.year DESC
        """,
            (selected_age_group, selected_event),
        )
    #This is for incase they mess with the submit method and try to submit somthing that is not in the database.
    if not cur or not selected_event or not selected_age_group:
        return render_template("404.html"), 404

    record = cur.fetchall()
    return render_template("records.html", record=record)


@app.errorhandler(404)
def invalid_route(_error):
    """Takes the user to an error 404 page if they try to go to a page that does not exist."""
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
