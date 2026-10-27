import sqlite3
from pathlib import Path
DB=Path(__file__).parent/'data'/'trends.db'
def connect():
    DB.parent.mkdir(exist_ok=True)
    conn=sqlite3.connect(DB,timeout=20)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS videos (video_id TEXT PRIMARY KEY,title TEXT,channel TEXT,published_at TEXT,url TEXT,duration_seconds INTEGER,last_seen TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS observations (video_id TEXT,market TEXT,category TEXT,observed_at TEXT,views INTEGER,likes INTEGER,comments INTEGER,PRIMARY KEY(video_id,market,category,observed_at))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS saved (video_id TEXT PRIMARY KEY,saved_at TEXT DEFAULT CURRENT_TIMESTAMP,note TEXT DEFAULT '')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS external_reels (id INTEGER PRIMARY KEY AUTOINCREMENT,platform TEXT,url TEXT UNIQUE,title TEXT,category TEXT,market TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    return conn
