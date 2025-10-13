-- cameras
CREATE TABLE IF NOT EXISTS cameras (
  id SERIAL PRIMARY KEY,
  name TEXT,
  location TEXT,
  api_key TEXT,
  rotate BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT now()
);

-- watchlist
CREATE TABLE IF NOT EXISTS watchlist (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  image_url TEXT,
  embedding BYTEA,
  added_by TEXT,
  added_at TIMESTAMP DEFAULT now()
);

-- events
CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  camera_id INT REFERENCES cameras(id) ON DELETE SET NULL,
  event_type TEXT, -- 'weapon'|'face'|'suspicious'
  timestamp TIMESTAMP DEFAULT now(),
  image_url TEXT,
  local_path TEXT,
  weapon_detected BOOLEAN DEFAULT FALSE,
  weapon_conf FLOAT,
  watchlist_id INT REFERENCES watchlist(id),
  watchlist_score FLOAT,
  suspicious BOOLEAN DEFAULT FALSE,
  confirmed BOOLEAN DEFAULT FALSE,
  model_versions JSONB,
  meta JSONB
);

-- detections
CREATE TABLE IF NOT EXISTS detections (
  id SERIAL PRIMARY KEY,
  event_id INT REFERENCES events(id) ON DELETE CASCADE,
  label TEXT,
  conf FLOAT,
  bbox JSONB
);

-- admin users (simple)
CREATE TABLE IF NOT EXISTS admins (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE,
  name TEXT,
  password_hash TEXT,
  created_at TIMESTAMP DEFAULT now()
);
