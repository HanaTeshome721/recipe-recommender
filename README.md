Recipe Recommender

Flask User Management API

A simple Flask + SQLAlchemy + MySQL/PostgreSQL project that provides user authentication and session management.
Supports login, logout, and protected routes using Flask-Login and cookies.

🚀 Features

User registration & login with password hashing

Session management using cookies

Protected routes that require authentication

Works with MySQL (local) and PostgreSQL (Render deployment)

RESTful API endpoints tested with curl

📂 Project Structure
.
├── app.py                # Main Flask app entry
├── models.py             # SQLAlchemy models
├── routes/               # API routes (users, auth, etc.)
├── requirements.txt      # Python dependencies
├── README.md             # Documentation
└── ...

⚙️ Setup (Local Development)

Clone repository

git clone https://github.com/your-username/flask-user-api.git
cd flask-user-api


Create virtual environment

python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows


Install dependencies

pip install -r requirements.txt


Configure database

For MySQL local dev, create a database:

CREATE DATABASE flask_users;


Copy .env.example → .env and set:

DATABASE_URL=mysql+pymysql://root:password@localhost/flask_users
SECRET_KEY=your-secret-key


Run migrations & start app

flask db upgrade
flask run

🌐 Deployment on Render

Push project to GitHub.

On Render
:

Create a new Web Service → Connect to GitHub repo.

Select runtime: Python 3.

Set Start Command:

gunicorn app:app


Add Environment Variables in Render:

SECRET_KEY=your-secret-key
DATABASE_URL=postgres://<user>:<pass>@<host>:5432/<dbname>


(Use the connection string from your Render PostgreSQL instance)

Redeploy your service.

🔑 API Usage
1. List users
curl http://localhost:5000/users

2. Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}' \
  -c cookies.txt

3. Protected Logout (with saved cookie)
curl -X POST http://localhost:5000/logout -b cookies.txt

📦 Requirements

Main dependencies:

Flask

Flask-SQLAlchemy

Flask-Migrate

Flask-Login

PyMySQL (for MySQL local)

psycopg2-binary (for PostgreSQL on Render)

gunicorn (for deployment)
