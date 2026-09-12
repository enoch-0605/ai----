ALTER TABLE game_session
    ADD COLUMN user_id VARCHAR(64) NULL,
    ADD INDEX ix_game_session_user_id (user_id);
