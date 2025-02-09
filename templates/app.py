from flask import Flask, render_template, request, redirect, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

# 📌 Create database table if it does not exist
def create_database():
    conn = sqlite3.connect("signup.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,  -- Now stores hashed passwords
            user_type TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

create_database()

# 📌 Serve the signup page
@app.route("/")
def home():
    return render_template("signup.html")  

# 📌 Handle form submission
@app.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")

    # Get user type (default to "USER" if none selected)
    user_type = "USER" if request.form.get("user") else "COLLECTOR"

    # Hash password before storing
    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect("signup.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO users (name, email, password, user_type) VALUES (?, ?, ?, ?)",
                       (name, email, hashed_password, user_type))
        conn.commit()
        conn.close()
        flash("Signup successful! Please log in.", "success")
        return redirect("/")  
    except sqlite3.IntegrityError:
        flash("Error: Email already exists!", "error")
        return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
