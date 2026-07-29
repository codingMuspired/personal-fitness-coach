-- Run after the original schema.
-- This first personal version uses the publishable/anon key behind a private Streamlit app.
-- Policies are restricted to profile_id = 1 where possible.

create index if not exists ix_body_measurements_profile_date on body_measurements(profile_id, measured_on desc);
create index if not exists ix_workout_sessions_profile_date on workout_sessions(profile_id, scheduled_date desc);
create index if not exists ix_running_sessions_profile_date on running_sessions(profile_id, run_date desc);
create index if not exists ix_daily_nutrition_profile_date on daily_nutrition(profile_id, log_date desc);
create index if not exists ix_exercise_sets_session on exercise_sets(workout_session_id);

alter table profiles enable row level security;
alter table body_measurements enable row level security;
alter table exercises enable row level security;
alter table workout_sessions enable row level security;
alter table exercise_sets enable row level security;
alter table running_sessions enable row level security;
alter table running_benchmarks enable row level security;
alter table nutrition_targets enable row level security;
alter table daily_nutrition enable row level security;
alter table race_goals enable row level security;
alter table weekly_reviews enable row level security;

-- Drop/recreate makes this script rerunnable.
drop policy if exists "personal profile read" on profiles;
create policy "personal profile read" on profiles for select to anon using (profile_id = 1);

drop policy if exists "personal measurements" on body_measurements;
create policy "personal measurements" on body_measurements for all to anon using (profile_id = 1) with check (profile_id = 1);

drop policy if exists "exercise catalog read" on exercises;
create policy "exercise catalog read" on exercises for select to anon using (true);

drop policy if exists "personal workouts" on workout_sessions;
create policy "personal workouts" on workout_sessions for all to anon using (profile_id = 1) with check (profile_id = 1);

drop policy if exists "personal exercise sets" on exercise_sets;
create policy "personal exercise sets" on exercise_sets for all to anon
using (exists (select 1 from workout_sessions ws where ws.workout_session_id = exercise_sets.workout_session_id and ws.profile_id = 1))
with check (exists (select 1 from workout_sessions ws where ws.workout_session_id = exercise_sets.workout_session_id and ws.profile_id = 1));

drop policy if exists "personal runs" on running_sessions;
create policy "personal runs" on running_sessions for all to anon using (profile_id = 1) with check (profile_id = 1);

drop policy if exists "personal benchmarks" on running_benchmarks;
create policy "personal benchmarks" on running_benchmarks for all to anon using (profile_id = 1) with check (profile_id = 1);

drop policy if exists "personal targets" on nutrition_targets;
create policy "personal targets" on nutrition_targets for all to anon using (profile_id = 1) with check (profile_id = 1);

drop policy if exists "personal nutrition" on daily_nutrition;
create policy "personal nutrition" on daily_nutrition for all to anon using (profile_id = 1) with check (profile_id = 1);

drop policy if exists "personal races" on race_goals;
create policy "personal races" on race_goals for all to anon using (profile_id = 1) with check (profile_id = 1);

drop policy if exists "personal reviews" on weekly_reviews;
create policy "personal reviews" on weekly_reviews for all to anon using (profile_id = 1) with check (profile_id = 1);

grant usage on schema public to anon;
grant select on profiles, exercises to anon;
grant select, insert, update, delete on body_measurements, workout_sessions, exercise_sets,
    running_sessions, running_benchmarks, nutrition_targets, daily_nutrition, race_goals, weekly_reviews to anon;
grant usage, select on all sequences in schema public to anon;
