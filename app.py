from flask import Flask, render_template
import sqlite3

app = Flask(__name__)

#from flask import Flask, g, render_template, request, redirect, url_for, session, flash


# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
# from sqlalchemy import String, Integer, ForeignKey, select

# from werkzeug.security import generate_password_hash, check_password_hash
# import os


# DATABASE = 'database.db'

# app = Flask(__name__)
# app.secret_key = os.environ.get("FLASK_SECRET", "change-this-to-a-random-secret")

# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
# db = SQLAlchemy(app)


# class Base(DeclarativeBase):
#     pass


# class displays(Base):
#     __tablename__ = "display"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     event_id: Mapped[int] = mapped_column(ForeignKey)
#     age_group_id: Mapped[int] = mapped_column(ForeignKey)
#     person_id: Mapped[int] = mapped_column(ForeignKey)
#     record_id: Mapped[int] = mapped_column(ForeignKey)


# class events(Base):
#     __tablename__ = "event"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String(80))


# class age_groups(Base):
#     __tablename__ = "age_group"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String(80))
#     password_hash: Mapped[str] = mapped_column(String(80))


# class persons(Base):
#     __tablename__ = "person"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String(80))


# class records(Base):
#     __tablename__ = "record"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     record: Mapped[str] = mapped_column(String(80))


@app.route("/")
def home():
    return render_template("home.html")



if __name__ == "__main__":
    app.run(debug=True)
