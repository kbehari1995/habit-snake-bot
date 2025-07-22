-- =============================
-- ENUM TYPES
-- =============================
DROP TYPE IF EXISTS habit_category CASCADE;
CREATE TYPE habit_category AS ENUM ('core', 'bonus');

DROP TYPE IF EXISTS habit_status_enum CASCADE;
CREATE TYPE habit_status_enum AS ENUM ('⏭️', '⛔', '❌', '✅');

DROP TYPE IF EXISTS habit_marked_by_enum CASCADE;
CREATE TYPE habit_marked_by_enum AS ENUM ('auto', 'manual');

DROP TYPE IF EXISTS user_status_enum CASCADE;
CREATE TYPE user_status_enum AS ENUM ('active', 'deceased');

DROP TYPE IF EXISTS score_type_enum CASCADE;
CREATE TYPE score_type_enum AS ENUM ('core', 'bonus', 'streak', 'announcement');

-- =============================
-- USERS TABLE
-- =============================
DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(100),
    nickname VARCHAR(50),
    user_moji VARCHAR(10),
    dob DATE,
    timezone VARCHAR(50),
    email VARCHAR(255),
    user_status user_status_enum DEFAULT 'active',
    last_born_on DATE DEFAULT CURRENT_DATE,
    last_died_on DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (user_id, username, nickname, user_moji, dob, timezone, email, user_status) VALUES
(1149075733, 'KD', 'KD', '😌', '1999-09-27', 'Asia/Kolkata', 'rushiashu10@gmail.com', 'deceased'),
(7273415313, 'Shweta', 'SS', '👺', '1990-10-02', 'Asia/Dubai', 'Shweta2hindu@gmail.com', 'deceased'),
(7921918964, 'Sonal', 'So', '🦦', '1988-10-02', 'Asia/Kolkata', 'sonalmonga.2@gmail.com', 'deceased'),
(934148984, 'Akash Bhosale', 'AB', '🧐', '1999-05-05', 'Asia/Kolkata', 'akashbhosale3259@gmail.com', 'deceased'),
(8011007823, 'Raksha', 'Shetty', '🔥', '1990-02-27', 'Asia/Dubai', 'raksha_shetty@hotmail.com', 'deceased'),
(7601874368, 'Kunj', 'KB', '🐯', '1995-07-13', 'Asia/Kolkata', 'kbehari1995@gmail.com', 'active');

SELECT * FROM users;

-- =============================
-- HABITS TABLE
-- =============================
DROP TABLE IF EXISTS habits CASCADE;
CREATE TABLE habits (
    habit_id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    username VARCHAR(100),
    year_month CHAR(7),
    habit_text VARCHAR(100),
    habit_type habit_category,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO habits (user_id, username, year_month, habit_text, habit_type) VALUES
(7601874368, 'Kunj', '202507', 'No Cigs🚬', 'core'),
(7601874368, 'Kunj', '202507', 'Daily Workout💪', 'core'),
(7601874368, 'Kunj', '202507', 'Read 10 Pages📖', 'core');

SELECT * FROM habits;

-- =============================
-- CORE HABIT LOG
-- =============================
DROP TABLE IF EXISTS core_habit_log CASCADE;
CREATE TABLE core_habit_log (
    core_log_id SERIAL PRIMARY KEY,
    for_date DATE,
    year_month CHAR(6),
    user_id BIGINT REFERENCES users(user_id),
    username VARCHAR(100),
    habit_id INT REFERENCES habits(habit_id),
    habit_text VARCHAR(100),
    habit_status habit_status_enum,
    marked_by habit_marked_by_enum,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


SELECT * FROM core_habit_log;

-- =============================
-- DND LOG
-- =============================
DROP TABLE IF EXISTS dnd_log CASCADE;
CREATE TABLE dnd_log (
    dnd_log_id SERIAL PRIMARY KEY,
    year_month CHAR(6),
    username VARCHAR(100),
    user_id BIGINT REFERENCES users(user_id),
    habit_id INT REFERENCES habits(habit_id),
    habit_text VARCHAR(100),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO dnd_log (year_month, username, user_id, habit_id, habit_text, start_date, end_date) VALUES
('202507', 'Kunj', 7601874368, 1, 'Meditate 🧘‍♂️', '2025-07-15', '2025-07-15');

SELECT * FROM dnd_log;

-- =============================
-- DAILY SCORE LOG (formerly core_streak_log)
-- =============================
DROP TABLE IF EXISTS daily_score_log CASCADE;
CREATE TABLE daily_score_log (
    score_log_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    for_date DATE,
    user_id BIGINT REFERENCES users(user_id),
    username VARCHAR(100),
    log_txt_json JSONB,
    score INT,
    score_type score_type_enum
);

SELECT * FROM daily_score_log;

-- =============================
-- SCORE COMPUTATION FUNCTION
-- =============================
DROP FUNCTION IF EXISTS compute_habit_score(BIGINT, DATE);
CREATE OR REPLACE FUNCTION compute_habit_score(user_id_input BIGINT, target_date DATE)
RETURNS INT AS $$
DECLARE
    r RECORD;
    has_tick BOOLEAN := FALSE;
    has_cross BOOLEAN := FALSE;
    cross_count INT := 0;
BEGIN
    FOR r IN
        SELECT habit_status
        FROM core_habit_log
        WHERE user_id = user_id_input AND for_date = target_date
    LOOP
        IF r.habit_status = '✅' THEN
            has_tick := TRUE;
        ELSIF r.habit_status = '❌' THEN
            has_cross := TRUE;
            cross_count := cross_count + 1;
        END IF;
    END LOOP;

    IF has_cross THEN
        RETURN -cross_count;
    ELSIF has_tick THEN
        RETURN 1;
    ELSE
        RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================
-- TRIGGER FUNCTION FOR DAILY SCORE LOG
-- =============================
DROP FUNCTION IF EXISTS insert_streak_log_if_complete();
CREATE OR REPLACE FUNCTION insert_streak_log_if_complete()
RETURNS TRIGGER AS $$
DECLARE
    habit_count INT;
    log_count INT;
    habit_row RECORD;
    total_score INT := 0;
    log_json JSONB := '[]';
BEGIN
    SELECT COUNT(*) INTO habit_count
    FROM habits
    WHERE user_id = NEW.user_id
      AND year_month = TO_CHAR(NEW.for_date, 'YYYYMM')
      AND habit_type = 'core';

    SELECT COUNT(*) INTO log_count
    FROM core_habit_log
    WHERE user_id = NEW.user_id AND for_date = NEW.for_date;

    IF habit_count = log_count THEN
        FOR habit_row IN
            SELECT habit_id, habit_text, habit_status
            FROM core_habit_log
            WHERE user_id = NEW.user_id AND for_date = NEW.for_date
        LOOP
            log_json := log_json || jsonb_build_object(
                'habit_id', habit_row.habit_id,
                'habit_text', habit_row.habit_text,
                'habit_status', habit_row.habit_status
            );
        END LOOP;

        total_score := compute_habit_score(NEW.user_id, NEW.for_date);

        DELETE FROM daily_score_log WHERE user_id = NEW.user_id AND for_date = NEW.for_date;

        INSERT INTO daily_score_log (for_date, user_id, username, log_txt_json, score, score_type)
        VALUES (NEW.for_date, NEW.user_id, NEW.username, log_json, total_score, 'core');
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =============================
-- MTD STREAK CALCULATOR FUNCTION
-- =============================
DROP FUNCTION IF EXISTS mtd_streak_calculator();
CREATE OR REPLACE FUNCTION mtd_streak_calculator()
RETURNS TRIGGER AS $$
DECLARE
    crnt_date DATE := NEW.for_date::DATE;
    month_start DATE := DATE_TRUNC('month', crnt_date)::DATE;
    active_users_count INT;
    core_entries_count INT;
    user_record RECORD;
    user_score INT;
    user_log_json JSONB;
BEGIN
    RAISE NOTICE '[BEGIN] mtd_streak_calculator(%), Month starts on %', crnt_date, month_start;

    -- List active users
    RAISE NOTICE '📋 Active Users:';
    FOR user_record IN SELECT user_id, username FROM users WHERE user_status = 'active'
    LOOP
        RAISE NOTICE ' - % (%): user_id = %', user_record.username, user_record.user_id, user_record.user_id;
    END LOOP;

    SELECT COUNT(*) INTO active_users_count
    FROM users WHERE user_status = 'active';

    SELECT COUNT(DISTINCT user_id) INTO core_entries_count
    FROM daily_score_log
    WHERE for_date::DATE = crnt_date
      AND score_type = 'core'
      AND user_id IN (SELECT user_id FROM users WHERE user_status = 'active');

    RAISE NOTICE '[DEBUG] Active users expected: %, Core logs found: %', active_users_count, core_entries_count;

    IF active_users_count = core_entries_count THEN
        RAISE NOTICE '[OK] All active users have core logs. Proceeding...';

        DELETE FROM daily_score_log
        WHERE for_date::DATE = crnt_date AND score_type = 'streak';

        FOR user_record IN
            SELECT user_id, username FROM users WHERE user_status = 'active'
        LOOP
            RAISE NOTICE '[USER] Now processing user % (%):', user_record.username, user_record.user_id;

            SELECT 
                COALESCE(SUM(score), 0),
                jsonb_agg(jsonb_build_object(
                    'date', for_date::TEXT,
                    'score', score
                ) ORDER BY for_date)
            INTO user_score, user_log_json
            FROM daily_score_log
            WHERE user_id = user_record.user_id
              AND score_type = 'core'
              AND for_date::DATE BETWEEN month_start AND crnt_date;

            RAISE NOTICE '[INSERT] Inserting streak for % (score = %)', user_record.username, user_score;

            INSERT INTO daily_score_log (
                for_date, user_id, username, log_txt_json, score, score_type
            )
            VALUES (
                crnt_date,
                user_record.user_id,
                user_record.username,
                COALESCE(user_log_json, '[]'::jsonb),
                user_score,
                'streak'
            );
        END LOOP;
    ELSE
        RAISE NOTICE '[SKIP] Mismatch: Active users = %, core entries = %. No streak logged.', active_users_count, core_entries_count;
    END IF;

    RAISE NOTICE '[COMPLETE] mtd_streak_calculator(%) done.', crnt_date;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =============================
-- User Active/Inactive Function
-- =============================

DROP FUNCTION IF EXISTS mark_user_deceased_from_streak;
CREATE OR REPLACE FUNCTION mark_user_deceased_from_streak()
RETURNS TRIGGER AS $$
BEGIN
    -- Only mark as deceased if streak score is negative and user is currently active
    IF NEW.score_type = 'streak' AND NEW.score < 0 THEN
        UPDATE users
        SET user_status = 'deceased',
            last_died_on = NEW.for_date
        WHERE user_id = NEW.user_id
          AND user_status = 'active';
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- =============================
-- TRIGGER BINDING
-- =============================
DROP TRIGGER IF EXISTS trg_streak_log_insert ON core_habit_log;
CREATE TRIGGER trg_streak_log_insert
AFTER INSERT ON core_habit_log
FOR EACH ROW
EXECUTE FUNCTION insert_streak_log_if_complete();

DROP TRIGGER IF EXISTS trg_mtd_streak_calculator ON daily_score_log;
CREATE TRIGGER trg_mtd_streak_calculator
AFTER INSERT ON daily_score_log
FOR EACH ROW
WHEN (NEW.score_type = 'core')
EXECUTE FUNCTION mtd_streak_calculator();

DROP TRIGGER IF EXISTS trg_mark_user_deceased ON daily_score_log;
CREATE TRIGGER trg_mark_user_deceased
AFTER INSERT ON daily_score_log
FOR EACH ROW
WHEN (NEW.score_type = 'streak' AND NEW.score < 0)
EXECUTE FUNCTION mark_user_deceased_from_streak();


select * from users;
SELECT * FROM habits;
SELECT * FROM core_habit_log;

INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by) VALUES
('2025-07-01', '202507', 7601874368, 'Kunj', 1, 'No Cigs🚬', '✅', 'manual'),
('2025-07-01', '202507', 7601874368, 'Kunj', 2, 'Daily Workout💪', '✅', 'manual'),
('2025-07-01', '202507', 7601874368, 'Kunj', 3, 'Read 10 Pages📖', '✅', 'manual');

SELECT * FROM core_habit_log;
SELECT * FROM daily_score_log;

INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by) VALUES
('2025-07-02', '202507', 7601874368, 'Kunj', 1, 'No Cigs🚬', '✅', 'manual'),
('2025-07-02', '202507', 7601874368, 'Kunj', 2, 'Daily Workout💪', '✅', 'manual'),
('2025-07-02', '202507', 7601874368, 'Kunj', 3, 'Read 10 Pages📖', '✅', 'manual');

SELECT * FROM core_habit_log;
SELECT * FROM daily_score_log;

INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by) VALUES
('2025-07-03', '202507', 7601874368, 'Kunj', 1, 'No Cigs🚬', '✅', 'manual'),
('2025-07-03', '202507', 7601874368, 'Kunj', 2, 'Daily Workout💪', '❌', 'manual');

SELECT * FROM daily_score_log;

INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by) VALUES
('2025-07-03', '202507', 7601874368, 'Kunj', 3, 'Read 10 Pages📖', '⏭️', 'manual');

SELECT * FROM daily_score_log;

INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by) VALUES
('2025-07-04', '202507', 7601874368, 'Kunj', 1, 'No Cigs🚬', '⛔', 'manual'),
('2025-07-04', '202507', 7601874368, 'Kunj', 2, 'Daily Workout💪', '⛔', 'manual'),
('2025-07-04', '202507', 7601874368, 'Kunj', 3, 'Read 10 Pages📖', '⏭️', 'manual');

SELECT * FROM daily_score_log;


UPDATE users
SET user_status = 'active'
WHERE username = 'Sonal';

--(7921918964, 'Sonal', 'So', '🦦', '1988-10-02', 'Asia/Kolkata', 'sonalmonga.2@gmail.com', 'deceased'),

INSERT INTO habits (user_id, username, year_month, habit_text, habit_type) VALUES
(7921918964, 'Sonal', '202507', 'Walking🚶', 'core'),
(7921918964, 'Sonal', '202507', 'Breathing🫁', 'core');


select * from users;
SELECT * FROM habits;


SELECT * FROM core_habit_log;
SELECT * FROM daily_score_log;

INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by) VALUES
('2025-07-01', '202507', 7921918964, 'Sonal', 1, 'Walking🚶', '✅', 'manual'),
('2025-07-01', '202507', 7921918964, 'Sonal', 2, 'Breathing🫁', '✅', 'manual'),
('2025-07-02', '202507', 7921918964, 'Sonal', 1, 'Walking🚶', '❌', 'manual'),
('2025-07-02', '202507', 7921918964, 'Sonal', 2, 'Breathing🫁', '✅', 'manual'),
('2025-07-03', '202507', 7921918964, 'Sonal', 1, 'Walking🚶', '⏭️', 'manual'),
('2025-07-03', '202507', 7921918964, 'Sonal', 2, 'Breathing🫁', '⛔', 'manual');


SELECT * FROM core_habit_log;
SELECT * FROM daily_score_log;

INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by) VALUES
('2025-07-04', '202507', 7921918964, 'Sonal', 1, 'Walking🚶', '✅', 'manual'),
('2025-07-04', '202507', 7921918964, 'Sonal', 2, 'Breathing🫁', '❌', 'manual');

select * from users;
SELECT * FROM core_habit_log;
SELECT * FROM daily_score_log;

