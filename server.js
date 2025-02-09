const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const multer = require('multer');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

// Database Connection
const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'password',
    database: 'ecosnap'
});

db.connect(err => {
    if (err) throw err;
    console.log('MySQL Connected');
});

// User Registration
app.post('/register', async (req, res) => {
    const { username, email, password } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    const sql = 'INSERT INTO users (username, email, password) VALUES (?, ?, ?)';
    db.query(sql, [username, email, hashedPassword], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'User registered successfully' });
    });
});

// User Login
app.post('/login', (req, res) => {
    const { email, password } = req.body;
    const sql = 'SELECT * FROM users WHERE email = ?';
    db.query(sql, [email], async (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        if (results.length === 0) return res.status(401).json({ error: 'User not found' });
        
        const isValid = await bcrypt.compare(password, results[0].password);
        if (!isValid) return res.status(401).json({ error: 'Invalid credentials' });
        
        const token = jwt.sign({ id: results[0].id }, 'secretkey', { expiresIn: '1h' });
        res.json({ message: 'Login successful', token });
    });
});

// File Upload Configuration
const storage = multer.diskStorage({
    destination: './uploads/',
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});
const upload = multer({ storage });

// Waste Submission
app.post('/upload', upload.single('image'), (req, res) => {
    const { category, location, userId } = req.body;
    const imagePath = req.file.path;
    const sql = 'INSERT INTO waste_reports (category, location, image, user_id) VALUES (?, ?, ?, ?)';
    db.query(sql, [category, location, imagePath, userId], (err, result) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Report submitted successfully' });
    });
});

// Fetch Statistics
app.get('/statistics', (req, res) => {
    const sql = 'SELECT category, COUNT(*) as count FROM waste_reports GROUP BY category';
    db.query(sql, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

// Fetch Ranking
app.get('/ranking', (req, res) => {
    const sql = 'SELECT username, points FROM users ORDER BY points DESC LIMIT 10';
    db.query(sql, (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json(results);
    });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
