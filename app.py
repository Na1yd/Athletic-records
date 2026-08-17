import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "Cabbage tree"

DATABASE = "athletics.db"


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


# This is the login route which allows the user to log in and change records in the database.
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("athletics.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT id, password FROM admin_users WHERE username = ?", (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = username
            return redirect(url_for("home"))
        flash("Invalid login", "error")
    return render_template("login.html")


# For logging out of admin
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


# This is the admin change area where you can alter records and it requirs admin login
@app.route("/admin")
@login_required
def admin_panel():
    return render_template("admin.html")


# Admin database management
@app.route("/admin/manage", methods=["GET", "POST"])
@login_required
def manage_database():
    conn = sqlite3.connect("athletics.db")
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

    # Get events and age groups for forms
    cur.execute("SELECT id, name FROM event ORDER BY name")
    events = cur.fetchall()
    cur.execute("SELECT id, name FROM age_group ORDER BY name")
    age_groups = cur.fetchall()
    cur.execute("SELECT id, name FROM person ORDER BY name")
    people = cur.fetchall()

    conn.close()

    return render_template(
        "manage.html",
        records=records,
        events=events,
        age_groups=age_groups,
        people=people,
    )


# Update existing record
@app.route("/admin/update_record/<int:record_id>", methods=["POST"])
@login_required
def update_record(record_id):
    year = request.form.get("year")
    person_name = request.form.get("person_name")
    bhs_record = request.form.get("bhs_record")

    # Validate inputs
    if not year or not person_name or not bhs_record:
        flash("All fields are required!", "error")
        return redirect(url_for("manage_database"))

    conn = sqlite3.connect("athletics.db")
    cur = conn.cursor()

    # Get the current person_id from the record
    cur.execute("SELECT person_id FROM records WHERE id = ?", (record_id,))
    result = cur.fetchone()

    if not result:
        flash("Record not found!", "error")
        conn.close()
        return redirect(url_for("manage_database"))

    person_id = result[0]

    # Update the person's name (keep the same person_id)
    cur.execute("UPDATE person SET name = ? WHERE id = ?", (person_name, person_id))

    # Update only year and bhs_record in records (event, age_group, and person_id stay the same)
    cur.execute(
        """
        UPDATE records
        SET year = ?, bhs_record = ?
        WHERE id = ?
    """,
        (year, bhs_record, record_id),
    )

    if cur.rowcount == 0:
        flash("Failed to update record!", "error")
    else:
        flash("Record updated successfully!", "success")

    conn.commit()
    conn.close()

    return redirect(url_for("manage_database"))


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# This is the home route which displays the form that allows you to filter the records.
@app.route("/")
def home():
    conn = sqlite3.connect("athletics.db")
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
    conn.close()
    events = query_db("SELECT id, name FROM event;")
    age_groups = query_db("SELECT id, name FROM age_group;")
    return render_template(
        "home.html", records=records, events=events, age_groups=age_groups
    )


# This is the route for all the records in the database.
@app.route("/records")
def records_table():
    conn = sqlite3.connect("athletics.db")
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


# This is the route for the submission form on the home page that filters the records based on the selected event and age group.
@app.route("/submit", methods=["POST"])
def submit():
    selected_event = request.form.get("events")
    selected_age_group = request.form.get("age_groups")
    conn = sqlite3.connect("athletics.db")
    cur = conn.cursor()
    # This is in case both are set to defult. Does the same thing as the all records route.
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
    # This is for if they select all boys records from a all events.
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
    # This is for if they select all girls records from a all events.
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
    # This is for if they select all track event records from all year groups.
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
    # This is for if they select all field event records from all year groups.
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
    # This is for if they select all boys records from all field events.
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
    # This is for if they select all boys records from all track events.
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
    # This is for if they select all girls records from all field events.
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
    # This is for if they select all girls records from all track events.
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
    # This is for if they select all boys records from a specific event.
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
    # This is for if they select all girls records from a specific event.
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
    # This is for if they select all track records from a specific age group.
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
    # This is for if they select all field records from a specific age group.
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
    # This is for if they select all events and one age group. It will show all
    # events records for that age group.
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
    # This is for if they select all age groups and one event. It will show all age group records for that one specific event.
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
    # This is for if they want a specific record for that age group and event.
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
    # This is for incase they mess with the submit method and try to submit somthing that is not in the database.
    if not cur or not selected_event or not selected_age_group:
        return render_template("404.html"), 404

    record = cur.fetchall()
    conn.close()
    return render_template("records.html", record=record)


# If they try to go to a page that does not exist then it will give them this error mesage
@app.errorhandler(404)
def invalid_route(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
