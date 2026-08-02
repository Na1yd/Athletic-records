from flask import Flask, render_template, request, g
import sqlite3

app = Flask(__name__)

DATABASE = "athletics.db"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

#testing commit
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


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
    return render_template("home.html", records=records, events=events, 
                           age_groups=age_groups)


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
    return render_template('records.html', record=record)


@app.route('/submit', methods=['POST'])
def submit():
    selected_event = request.form.get('events')
    selected_age_group = request.form.get('age_groups')
    conn = sqlite3.connect("athletics.db")
    cur = conn.cursor()

    if selected_event == "All events" and selected_age_group == "All years":
         cur.execute('''
            SELECT records.id, records.year, event.name, age_group.name, person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            ORDER BY records.year DESC
        ''',)
         
    elif selected_event == "All events":
            cur.execute('''
                SELECT records.id, records.year, event.name, age_group.name, person.name, records.bhs_record
                FROM records
                INNER JOIN event ON records.event_id = event.id
                INNER JOIN age_group ON records.age_group_id = age_group.id
                INNER JOIN person ON records.person_id = person.id
                WHERE records.age_group_id = ?
                ORDER BY records.year DESC
            ''', (selected_age_group))

    elif selected_age_group == "All years":
            cur.execute('''
                SELECT records.id, records.year, event.name, age_group.name, person.name, records.bhs_record
                FROM records
                INNER JOIN event ON records.event_id = event.id
                INNER JOIN age_group ON records.age_group_id = age_group.id
                INNER JOIN person ON records.person_id = person.id
            WHERE records.event_id = ?
                ORDER BY records.year DESC
            ''', (selected_event))
    else:
        cur.execute('''
            SELECT records.id, records.year, event.name, age_group.name, person.name, records.bhs_record
            FROM records
            INNER JOIN event ON records.event_id = event.id
            INNER JOIN age_group ON records.age_group_id = age_group.id
            INNER JOIN person ON records.person_id = person.id
            WHERE records.age_group_id = ? AND records.event_id = ?
            ORDER BY records.year DESC
        ''', (selected_age_group, selected_event))

    record = cur.fetchall()
    conn.close()
    return render_template('records.html', record=record)


if __name__ == "__main__":
    app.run(debug=True)
