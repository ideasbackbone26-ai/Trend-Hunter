"""Shared database interface: PostgreSQL via SUPABASE_DB_URL, otherwise local SQLite.
Do not commit .env or database credentials.
"""
import os
import re
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / '.env')
DB = Path(__file__).resolve().parent / 'data' / 'trends.db'

class PostgresConnection:
    def __init__(self, url):
        import psycopg
        from psycopg.rows import dict_row
        self.conn = psycopg.connect(url, row_factory=dict_row, connect_timeout=15)

    def execute(self, query, params=()):
        # Only the project's own static SQL queries are accepted here.
        query = re.sub(r'\bINSERT\s+OR\s+IGNORE\s+INTO\b', 'INSERT INTO', query, flags=re.I)
        if 'INSERT INTO saved' in query and 'saved_at' not in query:
            query = query.replace('saved(video_id)', 'saved(video_id,saved_at)')
            query = query.replace('VALUES(?)', 'VALUES(?,CURRENT_TIMESTAMP)')
        if 'INSERT INTO external_reels' in query and 'created_at' not in query:
            query = query.replace('external_reels(platform,url,title,category,market)', 'external_reels(platform,url,title,category,market,created_at)')
            query = query.replace('VALUES(?,?,?,?,?)', 'VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)')
        if re.search(r'INSERT\s+INTO\s+(saved|observations|external_reels)\b', query, re.I) and 'ON CONFLICT' not in query.upper():
            query += ' ON CONFLICT DO NOTHING'
        query = query.replace('?', '%s')
        return self.conn.execute(query, params)

    def __enter__(self):
        self.conn.__enter__()
        return self

    def __exit__(self, *args):
        return self.conn.__exit__(*args)

    def close(self):
        self.conn.close()


def connect():
    url = os.getenv('SUPABASE_DB_URL', '').strip()
    if url:
        return PostgresConnection(url)
    DB.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS videos (video_id TEXT PRIMARY KEY,title TEXT,channel TEXT,published_at TEXT,url TEXT,duration_seconds INTEGER,last_seen TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS observations (video_id TEXT,market TEXT,category TEXT,observed_at TEXT,views INTEGER,likes INTEGER,comments INTEGER,PRIMARY KEY(video_id,market,category,observed_at))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS saved (video_id TEXT PRIMARY KEY,saved_at TEXT DEFAULT CURRENT_TIMESTAMP,note TEXT DEFAULT '')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS external_reels (id INTEGER PRIMARY KEY AUTOINCREMENT,platform TEXT,url TEXT UNIQUE,title TEXT,category TEXT,market TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    return conn
