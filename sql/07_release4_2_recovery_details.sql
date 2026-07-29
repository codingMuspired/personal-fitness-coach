-- Release 4.2: detailed active-recovery and mobility prescriptions

CREATE TABLE IF NOT EXISTS prescribed_recovery_exercises
(
    prescribed_recovery_exercise_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    weekly_plan_session_id           BIGINT NOT NULL REFERENCES weekly_plan_sessions(weekly_plan_session_id) ON DELETE CASCADE,
    exercise_order                   INTEGER NOT NULL,
    exercise_name                    TEXT NOT NULL,
    category                         TEXT NOT NULL,
    target_sets                      INTEGER NOT NULL DEFAULT 1 CHECK (target_sets >= 1),
    target_repetitions               INTEGER,
    target_duration_seconds          INTEGER,
    side_instruction                 TEXT,
    target_rpe                       NUMERIC(3,1),
    notes                            TEXT,
    is_optional                      BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE(weekly_plan_session_id, exercise_order)
);

CREATE INDEX IF NOT EXISTS ix_prescribed_recovery_session_order
    ON prescribed_recovery_exercises(weekly_plan_session_id, exercise_order);

ALTER TABLE prescribed_recovery_exercises ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS personal_prescribed_recovery_exercises ON prescribed_recovery_exercises;
CREATE POLICY personal_prescribed_recovery_exercises ON prescribed_recovery_exercises
FOR ALL TO anon, authenticated
USING (
    EXISTS (
        SELECT 1
        FROM weekly_plan_sessions s
        WHERE s.weekly_plan_session_id = prescribed_recovery_exercises.weekly_plan_session_id
          AND s.profile_id = 1
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM weekly_plan_sessions s
        WHERE s.weekly_plan_session_id = prescribed_recovery_exercises.weekly_plan_session_id
          AND s.profile_id = 1
    )
);
