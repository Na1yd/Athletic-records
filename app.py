from flask import Flask, render_template, request, g
import sqlite3

app = Flask(__name__)

DATABASE = "athletics.db"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


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
    events = query_db("SELECT * FROM event;")
    conn.close()
    return render_template("home.html", events=events)


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


#@app.route('/submit', methods=['POST'])
#def submit():
    # 'car_brand' matches the name attribute in HTML
    #selected_value = request.form.get('events') 
    #conn = sqlite3.connect("athletics.db")
    #cur = conn.cursor()
    #cur.execute("""
                #SELECT records.id, records.year, age_group.name,
                #person.name, records.bhs_record
                #FROM records
                #INNER JOIN event ON records.event_id = event.id
                #INNER JOIN age_group ON records.age_group_id = age_group.id
                #INNER JOIN person ON records.person_id = person.id
                #""")
   #record = cur.fetchall()
    #return render_template('records.html', {selected_value})


@app.route('/submit', methods=['POST'])
def submit():
    selected_value = request.form.get('events')
    conn = sqlite3.connect("athletics.db")
    cur = conn.cursor()
    cur.execute("""
                SELECT records.id, records.year, event.name, age_group.name,
                person.name, records.bhs_record
                FROM records
                INNER JOIN event ON records.event_id = event.id
                INNER JOIN age_group ON records.age_group_id = age_group.id
                INNER JOIN person ON records.person_id = person.id
                WHERE records.event_id = ?
                ORDER BY records.year DESC
                """, (selected_value,))
    record = cur.fetchall()
    conn.close()
    return render_template('records.html', record=record)


if __name__ == "__main__":
    app.run(debug=True)
