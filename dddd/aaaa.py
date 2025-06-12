CREATE TABLE IF NOT EXISTS politicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    party TEXT
);

CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    politician_id INTEGER,
    title TEXT,
    content TEXT,
    pub_date TEXT,
    link TEXT,
    label TEXT,
    score REAL,
    FOREIGN KEY(politician_id) REFERENCES politicians(id)
);
