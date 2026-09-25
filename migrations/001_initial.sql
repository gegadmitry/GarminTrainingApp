CREATE TABLE activities (
    id INTEGER PRIMARY KEY,
    garmin_activity_id TEXT NOT NULL UNIQUE,
    sport TEXT NOT NULL CHECK (sport IN ('run', 'cycling', 'pool_swim', 'unknown')),
    start_time_utc TEXT NOT NULL,
    duration_seconds REAL NOT NULL CHECK (duration_seconds >= 0),
    distance_meters REAL CHECK (distance_meters IS NULL OR distance_meters >= 0),
    calories REAL CHECK (calories IS NULL OR calories >= 0),
    average_heart_rate INTEGER CHECK (average_heart_rate IS NULL OR average_heart_rate >= 0),
    max_heart_rate INTEGER CHECK (max_heart_rate IS NULL OR max_heart_rate >= 0),
    elevation_gain_meters REAL,
    imported_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    data_quality_status TEXT NOT NULL DEFAULT 'unvalidated'
        CHECK (data_quality_status IN ('unvalidated', 'valid', 'partial', 'invalid'))
);

CREATE TABLE activity_samples (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    recorded_at_utc TEXT NOT NULL,
    elapsed_seconds REAL NOT NULL CHECK (elapsed_seconds >= 0),
    heart_rate INTEGER CHECK (heart_rate IS NULL OR heart_rate >= 0),
    cadence REAL CHECK (cadence IS NULL OR cadence >= 0),
    speed_meters_per_second REAL CHECK (
        speed_meters_per_second IS NULL OR speed_meters_per_second >= 0
    ),
    distance_meters REAL CHECK (distance_meters IS NULL OR distance_meters >= 0)
);

CREATE TABLE activity_laps (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    lap_number INTEGER NOT NULL CHECK (lap_number > 0),
    duration_seconds REAL NOT NULL CHECK (duration_seconds >= 0),
    distance_meters REAL CHECK (distance_meters IS NULL OR distance_meters >= 0),
    UNIQUE(activity_id, lap_number)
);

CREATE TABLE health_records (
    id INTEGER PRIMARY KEY,
    recorded_at_utc TEXT NOT NULL,
    record_type TEXT NOT NULL,
    value REAL,
    unit TEXT,
    source TEXT NOT NULL DEFAULT 'garmin'
);

CREATE TABLE training_load (
    id INTEGER PRIMARY KEY,
    activity_id INTEGER REFERENCES activities(id) ON DELETE CASCADE,
    recorded_at_utc TEXT NOT NULL,
    training_effect_aerobic REAL,
    training_effect_anaerobic REAL,
    load_value REAL,
    recovery_seconds INTEGER CHECK (recovery_seconds IS NULL OR recovery_seconds >= 0)
);

CREATE TABLE sync_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE activity_provenance (
    activity_id INTEGER PRIMARY KEY REFERENCES activities(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    imported_at_utc TEXT NOT NULL,
    raw_file_path TEXT,
    raw_file_hash TEXT
);

CREATE TABLE running_metrics (
    activity_id INTEGER PRIMARY KEY REFERENCES activities(id) ON DELETE CASCADE,
    pace_seconds_per_kilometer REAL CHECK (
        pace_seconds_per_kilometer IS NULL OR pace_seconds_per_kilometer >= 0
    ),
    cadence_spm REAL CHECK (cadence_spm IS NULL OR cadence_spm >= 0),
    elevation_gain_meters REAL
);

CREATE TABLE cycling_metrics (
    activity_id INTEGER PRIMARY KEY REFERENCES activities(id) ON DELETE CASCADE,
    speed_meters_per_second REAL CHECK (
        speed_meters_per_second IS NULL OR speed_meters_per_second >= 0
    ),
    cadence_rpm REAL CHECK (cadence_rpm IS NULL OR cadence_rpm >= 0),
    power_watts REAL CHECK (power_watts IS NULL OR power_watts >= 0),
    elevation_gain_meters REAL
);

CREATE TABLE pool_swimming_metrics (
    activity_id INTEGER PRIMARY KEY REFERENCES activities(id) ON DELETE CASCADE,
    pool_length_meters REAL CHECK (pool_length_meters IS NULL OR pool_length_meters > 0),
    lengths INTEGER CHECK (lengths IS NULL OR lengths >= 0),
    pace_seconds_per_100m REAL CHECK (
        pace_seconds_per_100m IS NULL OR pace_seconds_per_100m >= 0
    ),
    average_stroke_count REAL CHECK (
        average_stroke_count IS NULL OR average_stroke_count >= 0
    ),
    swolf REAL CHECK (swolf IS NULL OR swolf >= 0),
    rest_seconds REAL CHECK (rest_seconds IS NULL OR rest_seconds >= 0),
    stroke_type TEXT
);