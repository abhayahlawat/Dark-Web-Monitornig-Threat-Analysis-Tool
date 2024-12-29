import sqlite3

DB_NAME = "darkweb_data.db"

def initialize_database():
    """Create the database and table if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            keywords TEXT,
            sentiment REAL,
            content_snippet TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(url, keywords, sentiment, content_snippet):
    """Insert a new record into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scraped_data (url, keywords, sentiment, content_snippet)
        VALUES (?, ?, ?, ?)
    ''', (url, ', '.join(keywords), sentiment, content_snippet))
    conn.commit()
    conn.close()
    print(f"Data saved for URL: {url}")
