from __future__ import annotations

import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path

import win32clipboard
import win32con
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "clipboard_data.db"

app = Flask(__name__)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_entry(text: str) -> None:
    cleaned = (text or "").strip()
    if not cleaned:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO clipboard_entries (text, created_at) VALUES (?, ?)",
            (cleaned, timestamp),
        )
        conn.commit()


def init_db() -> None:
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clipboard_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def get_windows_clipboard_text() -> str:
    try:
        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) or ""
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_TEXT):
                value = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                if isinstance(value, bytes):
                    return value.decode("utf-8", errors="replace")
                return value or ""
            return ""
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        return ""


def start_clipboard_watcher() -> None:
    if not hasattr(__import__('sys'), 'platform') or __import__('sys').platform != "win32":
        return

    last_text = ""
    last_save_time = 0.0
    stop_event = threading.Event()

    def worker() -> None:
        nonlocal last_text, last_save_time
        while not stop_event.is_set():
            current_text = get_windows_clipboard_text()
            now = time.monotonic()

            if current_text and current_text != last_text:
                if now - last_save_time > 0.8 or not last_text:
                    save_entry(current_text)
                    last_text = current_text
                    last_save_time = now
            elif not current_text:
                last_text = ""

            time.sleep(0.7)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    app.clipboard_watcher = {"thread": thread, "stop_event": stop_event}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/entries", methods=["GET", "POST"])
def entries_api():
    if request.method == "GET":
        date_filter = request.args.get("date", "").strip()
        query = request.args.get("q", "").strip()

        sql = "SELECT id, text, created_at FROM clipboard_entries"
        params = []
        clauses = []

        if date_filter:
            clauses.append("DATE(created_at) = ?")
            params.append(date_filter)

        if query:
            clauses.append("text LIKE ?")
            params.append(f"%{query}%")

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += " ORDER BY created_at DESC"

        with get_db_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        entries = [
            {
                "id": row["id"],
                "text": row["text"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
        return jsonify(entries)

    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()

    if not text:
        return jsonify({"error": "Clipboard text is required."}), 400

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO clipboard_entries (text, created_at) VALUES (?, ?)",
            (text, timestamp),
        )
        conn.commit()

    return jsonify({"success": True, "id": cursor.lastrowid, "created_at": timestamp})


@app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id: int):
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM clipboard_entries WHERE id = ?", (entry_id,))
        conn.commit()

    if cursor.rowcount == 0:
        return jsonify({"error": "Entry not found."}), 404

    return jsonify({"success": True, "deleted_id": entry_id})


init_db()
start_clipboard_watcher()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
