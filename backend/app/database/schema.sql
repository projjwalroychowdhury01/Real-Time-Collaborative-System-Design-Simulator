-- ============================================================
-- Real-Time Collaborative System Design Simulator
-- PostgreSQL Schema (Phase 1)
-- ============================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    username    VARCHAR(128) UNIQUE NOT NULL,
    auth_provider VARCHAR(50),          -- 'google' | 'github'
    auth_id     VARCHAR(255) UNIQUE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- Designs table
CREATE TABLE IF NOT EXISTS designs (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    design_json JSONB,                  -- Serialized canvas state
    is_public   BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_designs_user_id ON designs(user_id);

-- Checkpoints table
CREATE TABLE IF NOT EXISTS checkpoints (
    id                SERIAL PRIMARY KEY,
    design_id         INT NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
    checkpoint_number INT NOT NULL,
    design_json       JSONB,            -- Snapshot at this checkpoint
    metadata          JSONB,            -- Optional annotations / tags
    created_at        TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_design_id ON checkpoints(design_id);

-- Collaboration sessions table
CREATE TABLE IF NOT EXISTS collaboration_sessions (
    id            SERIAL PRIMARY KEY,
    design_id     INT NOT NULL REFERENCES designs(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    creator_id    INT NOT NULL REFERENCES users(id),
    created_at    TIMESTAMP DEFAULT NOW(),
    expires_at    TIMESTAMP,
    active_users  INT DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sessions_token ON collaboration_sessions(session_token);

-- Session members table
CREATE TABLE IF NOT EXISTS session_members (
    id             SERIAL PRIMARY KEY,
    session_id     INT NOT NULL REFERENCES collaboration_sessions(id) ON DELETE CASCADE,
    user_id        INT NOT NULL REFERENCES users(id),
    joined_at      TIMESTAMP DEFAULT NOW(),
    cursor_x       FLOAT,
    cursor_y       FLOAT,
    last_heartbeat TIMESTAMP
);
