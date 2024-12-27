import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Paths to our two DB files (created by filters)
PUBLISHERS_DB_PATH = Path(__file__).parent / "publishers.db"
STOCK_DB_PATH = Path(__file__).parent / "stock_data.db"

def init_db():
    """
    Create the 'users' table in publishers.db if not exists.
    The 'publishers' table is created by filter1, but we'll ensure it too.
    """
    conn = sqlite3.connect(PUBLISHERS_DB_PATH)
    cursor = conn.cursor()

    # Ensure publishers table exists (filter1 typically does this)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS publishers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            publisher_code TEXT UNIQUE
        )
    """)

    # Create a 'users' table for storing contact/user info
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

@app.route("/api/publishers", methods=["GET"])
def get_publishers():
    """
    Return all publisher_code entries from publishers.db.
    Example response: {"publishers": ["AVK", "KMB", "ALK", ...]}
    """
    try:
        conn = sqlite3.connect(PUBLISHERS_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT publisher_code FROM publishers")
        rows = cursor.fetchall()
        conn.close()
        publishers = [row[0] for row in rows]
        return jsonify({"publishers": publishers}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/stock_data", methods=["GET"])
def get_stock_data():
    """
    Return the stock data for a given ?publisher=CODE from stock_data.db,
    sorted by date ASC.
    Example: /api/stock_data?publisher=AVK
    """
    publisher = request.args.get("publisher", "").strip()
    if not publisher:
        return jsonify({"error": "Missing 'publisher' query param"}), 400
    try:
        conn = sqlite3.connect(STOCK_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, price, quantity, max, min, avg, total_turnover
            FROM stock_data
            WHERE publisher_code = ?
            ORDER BY date ASC
        """, (publisher,))
        rows = cursor.fetchall()
        conn.close()

        data_list = []
        for row in rows:
            data_list.append({
                "date": row[0],
                "price": row[1],
                "volume": row[2],         # 'quantity' is volume
                "max": row[3],
                "min": row[4],
                "avg": row[5],
                "total_turnover": row[6]
            })

        return jsonify({"publisher": publisher, "records": data_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/users", methods=["POST"])
def create_user():
    """
    Expects JSON: { "name": "...", "email": "...", "message": "..." }
    Inserts a row into the 'users' table in publishers.db.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    message = data.get("message", "").strip()

    if not name or not email or not message:
        return jsonify({"error": "Missing name/email/message"}), 400

    try:
        conn = sqlite3.connect(PUBLISHERS_DB_PATH)
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO users (name, email, message, created_at)
            VALUES (?, ?, ?, ?)
        """, (name, email, message, now_str))
        conn.commit()
        conn.close()
        return jsonify({"status": "ok", "msg": "User info saved"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
