CREATE TABLE IF NOT EXISTS expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  spent_date TEXT NOT NULL,       -- 例: 2026-02-05
  category TEXT NOT NULL,         -- 例: 食費
  amount INTEGER NOT NULL,        -- 例: 1200
  memo TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
