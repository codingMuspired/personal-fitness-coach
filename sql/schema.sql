CREATE TABLE profiles
(
    profile_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    display_name     TEXT NOT NULL,
    birth_date       DATE,
    height_inches    NUMERIC(5,2),
    starting_weight  NUMERIC(6,2),
    goal_weight      NUMERIC(6,2),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE body_measurements
(
    measurement_id  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id      BIGINT NOT NULL REFERENCES profiles(profile_id),
    measured_on     DATE NOT NULL,
    weight_lb       NUMERIC(6,2) NOT NULL,
    waist_inches    NUMERIC(5,2),
    body_fat_percent NUMERIC(5,2),
    notes            TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(profile_id, measured_on)
);

CREATE TABLE exercises
(
    exercise_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    exercise_name     TEXT NOT NULL UNIQUE,
    category          TEXT NOT NULL,
    equipment         TEXT,
    movement_pattern  TEXT,
    home_alternative  TEXT,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE workout_sessions
(
    workout_session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id         BIGINT NOT NULL REFERENCES profiles(profile_id),
    scheduled_date     DATE,
    completed_at       TIMESTAMPTZ,
    workout_type       TEXT NOT NULL,
    location_type      TEXT,
    duration_minutes   INTEGER,
    overall_rpe        NUMERIC(3,1),
    soreness_before    INTEGER,
    sleep_hours        NUMERIC(3,1),
    pain_reported      BOOLEAN NOT NULL DEFAULT FALSE,
    notes              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE exercise_sets
(
    exercise_set_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workout_session_id BIGINT NOT NULL REFERENCES workout_sessions(workout_session_id)
                       ON DELETE CASCADE,
    exercise_id        BIGINT NOT NULL REFERENCES exercises(exercise_id),
    set_number         INTEGER NOT NULL,
    weight_lb          NUMERIC(7,2),
    repetitions        INTEGER,
    duration_seconds   INTEGER,
    distance_meters    NUMERIC(8,2),
    rpe                 NUMERIC(3,1),
    reps_in_reserve    NUMERIC(3,1),
    completed          BOOLEAN NOT NULL DEFAULT TRUE,
    notes              TEXT
);

CREATE TABLE running_sessions
(
    running_session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workout_session_id BIGINT REFERENCES workout_sessions(workout_session_id)
                       ON DELETE CASCADE,
    profile_id         BIGINT NOT NULL REFERENCES profiles(profile_id),
    run_date           DATE NOT NULL,
    run_type           TEXT NOT NULL,
    distance_miles     NUMERIC(6,2) NOT NULL,
    duration_seconds   INTEGER NOT NULL,
    average_heart_rate INTEGER,
    elevation_feet     INTEGER,
    average_rpe        NUMERIC(3,1),
    surface_type       TEXT,
    notes              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE running_benchmarks
(
    benchmark_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id         BIGINT NOT NULL REFERENCES profiles(profile_id),
    benchmark_date     DATE NOT NULL,
    distance_name      TEXT NOT NULL,
    distance_miles     NUMERIC(6,3) NOT NULL,
    duration_seconds   INTEGER NOT NULL,
    notes              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE nutrition_targets
(
    nutrition_target_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id          BIGINT NOT NULL REFERENCES profiles(profile_id),
    effective_date      DATE NOT NULL,
    calorie_target      INTEGER NOT NULL,
    protein_grams       INTEGER NOT NULL,
    carbohydrate_grams  INTEGER,
    fat_grams           INTEGER,
    reason              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE daily_nutrition
(
    daily_nutrition_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id        BIGINT NOT NULL REFERENCES profiles(profile_id),
    log_date          DATE NOT NULL,
    calories          INTEGER,
    protein_grams     INTEGER,
    carbohydrate_grams INTEGER,
    fat_grams         INTEGER,
    water_ounces      INTEGER,
    notes             TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(profile_id, log_date)
);

CREATE TABLE race_goals
(
    race_goal_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id         BIGINT NOT NULL REFERENCES profiles(profile_id),
    race_name          TEXT NOT NULL,
    race_type          TEXT NOT NULL,
    race_date          DATE,
    distance_miles     NUMERIC(6,2),
    target_seconds     INTEGER,
    status             TEXT NOT NULL DEFAULT 'Planned',
    notes              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE weekly_reviews
(
    weekly_review_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    profile_id         BIGINT NOT NULL REFERENCES profiles(profile_id),
    week_start_date    DATE NOT NULL,
    average_weight_lb  NUMERIC(6,2),
    workouts_planned   INTEGER,
    workouts_completed INTEGER,
    running_miles      NUMERIC(6,2),
    average_sleep      NUMERIC(4,2),
    average_rpe        NUMERIC(4,2),
    calorie_average    INTEGER,
    recommendation     TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(profile_id, week_start_date)
);