from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"

    # create tables on startup (dev convenience)
    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return render_template("index.html")

    # ----- Test endpoints for users -----
    @app.route("/create-user", methods=["POST"])
    def create_user():
        """
        POST JSON { "email": "...", "password": "..." }
        creates a user and returns id + email
        """
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "email and password required"}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "user already exists"}), 400
        u = User(email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        return jsonify({"id": u.id, "email": u.email, "created_at": u.created_at.isoformat()}), 201

    @app.route("/users", methods=["GET"])
    def list_users():
        users = User.query.order_by(User.id.desc()).all()
        return jsonify([{"id": u.id, "email": u.email, "created_at": u.created_at.isoformat()} for u in users])

    @app.route("/login", methods=["POST"])
    def login():
        """
        POST JSON { "email": "...", "password": "..." }
        returns a session cookie on success
        """
        data = request.get_json() or {}
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "email and password required"}), 400
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "invalid credentials"}), 401
        login_user(user)
        return jsonify({"message": "logged in", "user": {"id": user.id, "email": user.email}})

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        return jsonify({"message": "logged out"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
