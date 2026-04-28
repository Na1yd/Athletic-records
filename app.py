from flask import Flask, render_template
import sqlite3

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/display")
def all_characters():
    conn = sqlite3.connect("athletics.db")
    cur = conn.cursor()
    cur.execute('SELECT display.id , event.name FROM display INNER JOIN event '
                'ON display.event_id = event.id')
    displays = cur.fetchall()
    conn.close()
    return render_template('display.html', displays=displays)


if __name__ == "__main__":
    app.run(debug=True)

        # FROM display
        # LEFT JOIN event ON display.event_id = event.id
        # LEFT JOIN age_group ON display.age_group_id = age_group.id
        # LEFT JOIN person ON display.person_id = person.id
        # LEFT JOIN record ON display.record_id = record.id;
