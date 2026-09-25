CREATE TABLE weekly_reports (
    week_start_utc TEXT PRIMARY KEY,
    summary_json TEXT NOT NULL,
    generated_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);