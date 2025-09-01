from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from passlib.hash import bcrypt
from config import Config
from datetime import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv


# load env vars
# load env vars
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def generate_ai_recipe(ingredients: list[str]) -> str:
    """
    Calls OpenAI API to generate a recipe suggestion based on ingredients.
    """
    if not ingredients:
        return "Please select some ingredients first."

    prompt = f"""
    You are a helpful cooking assistant. 
    Suggest a creative, delicious recipe using ONLY these ingredients: {', '.join(ingredients)}.
    Return the recipe with:
    - Title
    - Short description
    - Step-by-step instructions
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",   # you can also use gpt-4o-mini if quota is tight
            messages=[
                {"role": "system", "content": "You are a master chef AI."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7,
        )

        # Some SDK versions use dict-like access
        if hasattr(response.choices[0].message, "content"):
            recipe = response.choices[0].message.content
        else:
            recipe = response.choices[0].message["content"]

        return recipe.strip()

    except Exception as e:
        return f"⚠️ Error generating recipe: {e}"

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()



# ------------------ MODELS ------------------ #
class User(UserMixin, db.Model):   # <-- Add UserMixin
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    purchases = db.relationship("Purchase", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password):
        return bcrypt.verify(password, self.password_hash)

    queries = db.relationship("AIQuery", back_populates="user", lazy=True)

class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    short_desc = db.Column(db.Text, nullable=False)
    full_text = db.Column(db.Text, nullable=False)
    created_by_ai = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    purchases = db.relationship("Purchase", backref="recipe", lazy=True)
    ingredients = db.relationship("RecipeIngredient", backref="recipe", lazy=True)


class Ingredient(db.Model):
    __tablename__ = "ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    recipes = db.relationship("RecipeIngredient", backref="ingredient", lazy=True)


class RecipeIngredient(db.Model):
    __tablename__ = "recipe_ingredients"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)


class Purchase(db.Model):
    __tablename__ = "purchases"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="NGN")
    status = db.Column(db.String(20), nullable=False, default="initiated")
    created_at = db.Column(db.DateTime, server_default=db.func.now())


class AIQuery(db.Model):
    __tablename__ = "ai_queries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    query_text = db.Column(db.Text, nullable=False)
    response_text = db.Column(db.Text)  # can be empty until AI responds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="queries")
# --------------------------------------------- #


def stub_generate(ingredients):
    """Local fallback recipe when the AI fails."""
    title = "Quick " + " & ".join(ingredients) + " Skillet"
    instructions = (
        "1. Prep ingredients: chop and season.\n"
        "2. Heat a skillet, add oil, cook onions until soft.\n"
        "3. Add main ingredient and cook through.\n"
        "4. Add remaining ingredients, simmer 5-10 minutes.\n"
        "5. Serve hot. Adjust salt and pepper to taste."
    )
    return f"{title}\n\nIngredients: {', '.join(ingredients)}\n\n{instructions}"


def generate_with_openai(ingredients, model="gpt-3.5-turbo"):
    """
    Call OpenAI and return the recipe text.
    Raises exception on failure so caller can fall back.
    """
    if not openai.api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    prompt = (
        f"Create a short recipe using the following ingredients: {', '.join(ingredients)}.\n\n"
        "Return a title, a one-line short description, and step-by-step instructions.\n"
        "Keep it concise and clear."
    )

    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=600,
    )

    # defensive extraction
    choices = resp.get("choices") or []
    if not choices:
        raise RuntimeError("OpenAI returned no choices")

    message = choices[0].get("message") or {}
    content = message.get("content") or message.get("text")  # be defensive
    if not content:
        raise RuntimeError("OpenAI response missing content")

    return content.strip()


# ------------------ APP FACTORY ------------------ #
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "login"  # redirect here if not logged in

    # ---------------- ROUTES ---------------- #
    @app.route("/")
    def index():
        if current_user.is_authenticated:
             return render_template("welcome.html", user_email=current_user.email)
            #  return f"Hello, {current_user.email}! <a href='/logout'>Logout</a> | <a href='/ingredients'>Pick Ingredients</a>"
        return render_template("index.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            # check if user exists
            if User.query.filter_by(email=email).first():
                flash("Email already registered!", "danger")
                return redirect(url_for("signup"))

            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login"))

        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                login_user(user)
                flash("Logged in successfully!", "success")
                return redirect(url_for("index"))
            else:
                flash("Invalid credentials.", "danger")
                return redirect(url_for("login"))

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

  # ------------- INGREDIENT PICKER + AI ------------- #
    @app.route("/ingredients", methods=["GET", "POST"])
    def ingredients():
        recipe = None
        if request.method == "POST":
            # collect chosen ingredients
            selected = request.form.getlist("ingredients")
            

            if selected:
                # don’t join here
                recipe = generate_ai_recipe(selected)


                # Save query + recipe to DB if you want
                new_query = AIQuery(
                    user_id=current_user.id,
                    query_text=", ".join(selected),
                    response_text=recipe
                )
                db.session.add(new_query)
                db.session.commit()

        return render_template("ingredients.html", recipe=recipe)


    # ------------- VIEW HISTORY OF AI RECIPES ------------- #
    @app.route("/history")
    @login_required
    def history():
        queries = AIQuery.query.filter_by(user_id=current_user.id).order_by(AIQuery.created_at.desc()).all()
        return render_template("history.html", queries=queries)

    return app

# ---------------- LOGIN MANAGER ---------------- #
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)