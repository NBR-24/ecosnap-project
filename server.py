from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import bcrypt
import jwt
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'ecosnap'

mysql = MySQL(app)

# Secret Key for JWT
SECRET_KEY = 'secretkey'

# File Upload Configuration
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# User Registration
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data['username']
    email = data['email']
    password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        mysql.connection.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

# User Login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({"id": user[0]}, SECRET_KEY, algorithm="HS256")
    return jsonify({"message": "Login successful", "token": token})

# Waste Submission (File Upload)
@app.route('/upload', methods=['POST'])
def upload():
    category = request.form.get('category')
    location = request.form.get('location')
    user_id = request.form.get('userId')

    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image = request.files['image']
    image_filename = secure_filename(image.filename)
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    image.save(image_path)

    cur = mysql.connection.cursor()
    try:
        cur.execute("INSERT INTO waste_reports (category, location, image, user_id) VALUES (%s, %s, %s, %s)",
                    (category, location, image_path, user_id))
        mysql.connection.commit()
        return jsonify({"message": "Report submitted successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

# Fetch Statistics
@app.route('/statistics', methods=['GET'])
def statistics():
    cur = mysql.connection.cursor()
    cur.execute("SELECT category, COUNT(*) as count FROM waste_reports GROUP BY category")
    results = cur.fetchall()
    cur.close()

    return jsonify([{"category": row[0], "count": row[1]} for row in results])

# Fetch Ranking
@app.route('/ranking', methods=['GET'])
def ranking():
    cur = mysql.connection.cursor()
    cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
    results = cur.fetchall()
    cur.close()

    return jsonify([{"username": row[0], "points": row[1]} for row in results])

if __name__ == '__main__':
    app.run(debug=True, port=5000)
