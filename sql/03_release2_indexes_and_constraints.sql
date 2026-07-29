-- Release 2 migration. Safe to run once after Release 1.

CREATE INDEX IF NOT EXISTS ix_running_benchmarks_profile_date
    ON running_benchmarks(profile_id, benchmark_date DESC);

CREATE INDEX IF NOT EXISTS ix_exercise_sets_exercise_session
    ON exercise_sets(exercise_id, workout_session_id DESC);

CREATE INDEX IF NOT EXISTS ix_daily_nutrition_profile_date_desc
    ON daily_nutrition(profile_id, log_date DESC);

CREATE INDEX IF NOT EXISTS ix_body_measurements_profile_date_desc
    ON body_measurements(profile_id, measured_on DESC);

-- Prevent duplicate named benchmark entries on the same day.
CREATE UNIQUE INDEX IF NOT EXISTS ux_running_benchmark_profile_date_distance
    ON running_benchmarks(profile_id, benchmark_date, distance_name);
