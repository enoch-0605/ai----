-- Provenance is currently stored in game_session.state_json for backward compatibility.
-- These additive columns are reserved for a normalized MySQL deployment.
ALTER TABLE game_session
  ADD COLUMN IF NOT EXISTS generation_mode VARCHAR(20) NULL,
  ADD COLUMN IF NOT EXISTS freshness_status VARCHAR(20) NULL,
  ADD COLUMN IF NOT EXISTS generation_error VARCHAR(64) NULL,
  ADD COLUMN IF NOT EXISTS last_generation_attempt VARCHAR(64) NULL;
