DROP TABLE IF EXISTS completed_hands;
CREATE TABLE
    completed_hands (
        id UUID PRIMARY KEY,
        game_state JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    );