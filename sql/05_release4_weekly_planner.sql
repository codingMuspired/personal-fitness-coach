-- Release 4: weekly plans, sessions, and exercise prescriptions

CREATE TABLE IF NOT EXISTS weekly_plans
(
    weekly_plan_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id           BIGINT NOT NULL REFERENCES profiles(profile_id),
    week_start_date      DATE NOT NULL,
    plan_name            TEXT NOT NULL,
    phase_name           TEXT NOT NULL DEFAULT 'Foundation',
    is_deload             BOOLEAN NOT NULL DEFAULT FALSE,
    target_run_miles     NUMERIC(6,2),
    status               TEXT NOT NULL DEFAULT 'Draft'
                         CHECK (status IN ('Draft','Approved','Active','Completed','Archived')),
    rationale            JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at          TIMESTAMPTZ,
    UNIQUE(profile_id, week_start_date)
);

CREATE TABLE IF NOT EXISTS weekly_plan_sessions
(
    weekly_plan_session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    weekly_plan_id         BIGINT NOT NULL REFERENCES weekly_plans(weekly_plan_id) ON DELETE CASCADE,
    profile_id             BIGINT NOT NULL REFERENCES profiles(profile_id),
    session_date           DATE NOT NULL,
    sequence_number        INTEGER NOT NULL,
    workout_type           TEXT NOT NULL,
    title                  TEXT NOT NULL,
    duration_minutes       INTEGER NOT NULL CHECK (duration_minutes >= 0),
    target_distance_miles  NUMERIC(6,2),
    intensity              TEXT NOT NULL DEFAULT 'Normal',
    instructions           TEXT NOT NULL,
    home_alternative       TEXT,
    status                 TEXT NOT NULL DEFAULT 'Planned'
                           CHECK (status IN ('Planned','Approved','Completed','Skipped','Moved','Cancelled')),
    moved_from_date        DATE,
    source_session_id      BIGINT REFERENCES weekly_plan_sessions(weekly_plan_session_id),
    completed_workout_session_id BIGINT REFERENCES workout_sessions(workout_session_id),
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(weekly_plan_id, session_date, sequence_number)
);

CREATE TABLE IF NOT EXISTS prescribed_exercises
(
    prescribed_exercise_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    weekly_plan_session_id BIGINT NOT NULL REFERENCES weekly_plan_sessions(weekly_plan_session_id) ON DELETE CASCADE,
    exercise_id            BIGINT REFERENCES exercises(exercise_id),
    exercise_name          TEXT NOT NULL,
    exercise_order         INTEGER NOT NULL,
    target_sets            INTEGER,
    target_repetitions     INTEGER,
    target_weight_lb       NUMERIC(7,2),
    target_duration_seconds INTEGER,
    target_distance_meters NUMERIC(8,2),
    target_rpe             NUMERIC(3,1),
    reps_in_reserve        NUMERIC(3,1),
    substitution_name      TEXT,
    notes                  TEXT,
    UNIQUE(weekly_plan_session_id, exercise_order)
);

CREATE INDEX IF NOT EXISTS ix_weekly_plans_profile_week
    ON weekly_plans(profile_id, week_start_date DESC);
CREATE INDEX IF NOT EXISTS ix_weekly_plan_sessions_profile_date
    ON weekly_plan_sessions(profile_id, session_date);
CREATE INDEX IF NOT EXISTS ix_prescribed_exercises_session_order
    ON prescribed_exercises(weekly_plan_session_id, exercise_order);

ALTER TABLE weekly_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_plan_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescribed_exercises ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS personal_weekly_plans ON weekly_plans;
CREATE POLICY personal_weekly_plans ON weekly_plans
FOR ALL TO anon, authenticated
USING (profile_id = 1)
WITH CHECK (profile_id = 1);

DROP POLICY IF EXISTS personal_weekly_plan_sessions ON weekly_plan_sessions;
CREATE POLICY personal_weekly_plan_sessions ON weekly_plan_sessions
FOR ALL TO anon, authenticated
USING (profile_id = 1)
WITH CHECK (profile_id = 1);

DROP POLICY IF EXISTS personal_prescribed_exercises ON prescribed_exercises;
CREATE POLICY personal_prescribed_exercises ON prescribed_exercises
FOR ALL TO anon, authenticated
USING (
    EXISTS (
        SELECT 1
        FROM weekly_plan_sessions s
        WHERE s.weekly_plan_session_id = prescribed_exercises.weekly_plan_session_id
          AND s.profile_id = 1
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM weekly_plan_sessions s
        WHERE s.weekly_plan_session_id = prescribed_exercises.weekly_plan_session_id
          AND s.profile_id = 1
    )
);
