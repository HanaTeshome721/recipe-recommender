# app.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

# --- test model ---
class Ping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(50), nullable=False)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/db-test")
    def db_test():
        # create tables if they don't exist
        db.create_all()
        # insert a row if empty
        if not Ping.query.first():
            test_row = Ping(message="Hello from MySQL!")
            db.session.add(test_row)
            db.session.commit()
        # fetch first row
        row = Ping.query.first()
        return f"DB Test: {row.message}"

    return app
