CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT,
    item_name TEXT,
    spec TEXT,
    lot TEXT
);

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER,
    location TEXT,
    qty INTEGER,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    item_code TEXT,
    qty INTEGER,
    location TEXT,
    created_at TEXT
);
