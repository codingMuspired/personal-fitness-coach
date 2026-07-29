-- Release 4.1: editable weekly schedule and detailed run prescriptions

ALTER TABLE weekly_plan_sessions
    ADD COLUMN IF NOT EXISTS pace_guidance TEXT,
    ADD COLUMN IF NOT EXISTS treadmill_guidance TEXT,
    ADD COLUMN IF NOT EXISTS run_structure_summary TEXT;

CREATE TABLE IF NOT EXISTS prescribed_run_segments
(
    prescribed_run_segment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    weekly_plan_session_id     BIGINT NOT NULL REFERENCES weekly_plan_sessions(weekly_plan_session_id) ON DELETE CASCADE,
    segment_order              INTEGER NOT NULL,
    segment_type               TEXT NOT NULL,
    label                      TEXT NOT NULL,
    repetitions                INTEGER NOT NULL DEFAULT 1 CHECK (repetitions >= 1),
    target_distance_miles      NUMERIC(6,3),
    target_duration_seconds    INTEGER,
    recovery_seconds           INTEGER,
    pace_min_seconds_per_mile  INTEGER,
    pace_max_seconds_per_mile  INTEGER,
    target_rpe                 NUMERIC(3,1),
    notes                      TEXT,
    UNIQUE(weekly_plan_session_id, segment_order)
);

CREATE INDEX IF NOT EXISTS ix_prescribed_run_segments_session_order
    ON prescribed_run_segments(weekly_plan_session_id, segment_order);

ALTER TABLE prescribed_run_segments ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS personal_prescribed_run_segments ON prescribed_run_segments;
CREATE POLICY personal_prescribed_run_segments ON prescribed_run_segments
FOR ALL TO anon, authenticated
USING (
    EXISTS (
        SELECT 1
        FROM weekly_plan_sessions s
        WHERE s.weekly_plan_session_id = prescribed_run_segments.weekly_plan_session_id
          AND s.profile_id = 1
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM weekly_plan_sessions s
        WHERE s.weekly_plan_session_id = prescribed_run_segments.weekly_plan_session_id
          AND s.profile_id = 1
    )
);
