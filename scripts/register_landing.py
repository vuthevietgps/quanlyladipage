import os, sqlite3

DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database.db')

def upsert_landing(subdomain: str, agent: str = '', original_filename: str = 'index.html'):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS landing_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subdomain TEXT UNIQUE NOT NULL,
        agent TEXT,
        global_site_tag TEXT,
        phone_tracking TEXT,
        zalo_tracking TEXT,
        form_tracking TEXT,
        hotline_phone TEXT,
        zalo_phone TEXT,
        google_form_link TEXT,
        status TEXT NOT NULL DEFAULT 'active',
        original_filename TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    # upsert
    c.execute("SELECT id FROM landing_pages WHERE subdomain=?", (subdomain,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE landing_pages SET agent=?, original_filename=?, updated_at=CURRENT_TIMESTAMP WHERE subdomain=?",
                  (agent, original_filename, subdomain))
        print(f"Updated landing: {subdomain}")
    else:
        c.execute("INSERT INTO landing_pages (subdomain, agent, status, original_filename) VALUES (?,?, 'active', ?)",
                  (subdomain, agent, original_filename))
        print(f"Inserted landing: {subdomain}")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    upsert_landing('vongtay-shopee', agent='')
