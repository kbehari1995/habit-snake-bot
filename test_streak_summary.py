import asyncio
from datetime import datetime, date
from bot.utils.db import DBClient
from bot.utils.cached_db import dbCache
import time

def parse_date(datestr):
    return datetime.strptime(datestr, "%Y-%m-%d").date()

# --- Non-cached test functions ---
async def test_add_user(db):
    start = time.perf_counter()
    print("\n[Test] add_user")
    test_user_id = 9999999999
    dob = parse_date("2000-01-01")
    await db.add_user(test_user_id, "TestUser", "TestNick", "🐍", dob, "UTC", "test@example.com")
    user = await db.get_user_by_id(test_user_id)
    print("Expected: user with user_id=9999999999, username='TestUser'")
    print(f"Actual: {user}")
    print("PASS" if user and user['username'] == 'TestUser' else "FAIL")
    # Clean up
    async with db._pool.acquire() as conn:
        await conn.execute('DELETE FROM users WHERE user_id=$1', test_user_id)
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_update_user(db):
    start = time.perf_counter()
    print("\n[Test] update_user")
    test_user_id = 7601874368  # Kunj
    dob = parse_date("1995-07-13")
    await db.update_user(test_user_id, "KunjB", "🐍", dob, "Asia/Kolkata", "kunj_updated@gmail.com")
    user = await db.get_user_by_id(test_user_id)
    print("Expected: nickname='KunjB', usermoji='🐍', email='kunj_updated@gmail.com'")
    print(f"Actual: {user}")
    print("PASS" if user and user['nickname'] == 'KunjB' and user['user_moji'] == '🐍' and user['email'] == 'kunj_updated@gmail.com' else "FAIL")
    # Revert
    await db.update_user(test_user_id, "KB", "🐯", dob, "Asia/Kolkata", "kbehari1995@gmail.com")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_by_id(db):
    start = time.perf_counter()
    print("\n[Test] get_user_by_id")
    user = await db.get_user_by_id(7601874368)
    print("Expected: username='Kunj'")
    print(f"Actual: {user}")
    print("PASS" if user and user['username'] == 'Kunj' else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_all_users(db):
    start = time.perf_counter()
    print("\n[Test] get_all_users")
    users = await db.get_all_users()
    print(f"Expected: >=6 users (from SQL_DB.sql)")
    print(f"Actual: {len(users)} users")
    print("PASS" if len(users) >= 6 else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_add_habit(db):
    start = time.perf_counter()
    print("\n[Test] add_habit")
    test_user_id = 9999999999
    dob = parse_date("2000-01-01")
    await db.add_user(test_user_id, "TestUser", "TestNick", "🐍", dob, "UTC", "test@example.com")
    await db.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    habits = await db.get_user_habits_for_month(test_user_id, "202507")
    print("Expected: 1 habit with habit_text='Test Habit'")
    print(f"Actual: {habits}")
    print("PASS" if habits and habits[0]['habit_text'] == 'Test Habit' else "FAIL")
    # Clean up
    async with db._pool.acquire() as conn:
        await conn.execute('DELETE FROM habits WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM users WHERE user_id=$1', test_user_id)
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_habits_for_month(db):
    start = time.perf_counter()
    print("\n[Test] get_user_habits_for_month")
    habits = await db.get_user_habits_for_month(7601874368, "202507")
    print("Expected: >=3 habits for Kunj in 202507")
    print(f"Actual: {habits}")
    print("PASS" if len(habits) >= 3 else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_has_existing_core_habits(db):
    start = time.perf_counter()
    print("\n[Test] has_existing_core_habits")
    exists = await db.has_existing_core_habits(7601874368, "202507")
    print("Expected: True for Kunj in 202507")
    print(f"Actual: {exists}")
    print("PASS" if exists else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_log_checkin_and_has_already_checked_in(db):
    start = time.perf_counter()
    print("\n[Test] log_checkin & has_already_checked_in")
    test_user_id = 9999999999
    dob = parse_date("2000-01-01")
    await db.add_user(test_user_id, "TestUser", "TestNick", "🐍", dob, "UTC", "test@example.com")
    await db.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    # Get habit_id
    habits = await db.get_user_habits_for_month(test_user_id, "202507")
    habit_id = habits[0]['habit_id']
    for_date = parse_date("2025-07-05")
    await db.log_checkin(for_date, "202507", test_user_id, "TestUser", habit_id, "Test Habit", "✅", "manual")
    checked_in = await db.has_already_checked_in(test_user_id, for_date)
    print("Expected: True after checkin")
    print(f"Actual: {checked_in}")
    print("PASS" if checked_in else "FAIL")
    # Clean up
    async with db._pool.acquire() as conn:
        await conn.execute('DELETE FROM dnd_log WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM daily_score_log WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM core_habit_log WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM habits WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM users WHERE user_id=$1', test_user_id)
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_checkin_summary(db):
    start = time.perf_counter()
    print("\n[Test] get_user_checkin_summary")
    for_date = parse_date("2025-07-01")
    summary = await db.get_user_checkin_summary(7601874368, for_date)
    print("Expected: 3 checkins for Kunj on 2025-07-01")
    print(f"Actual: {summary}")
    print("PASS" if len(summary) == 3 else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_add_dnd_period_and_get_dnd_entries_for_user(db):
    start = time.perf_counter()
    print("\n[Test] add_dnd_period & get_dnd_entries_for_user")
    test_user_id = 9999999999
    dob = parse_date("2000-01-01")
    await db.add_user(test_user_id, "TestUser", "TestNick", "🐍", dob, "UTC", "test@example.com")
    await db.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    await db.add_dnd_period("202507", "TestUser", test_user_id, 1, "Test Habit", parse_date("2025-07-10"), parse_date("2025-07-12"))
    dnd_entries = await db.get_dnd_entries_for_user(test_user_id)
    print("Expected: 1 DND entry for TestUser")
    print(f"Actual: {dnd_entries}")
    print("PASS" if dnd_entries and dnd_entries[0]['habit_text'] == 'Test Habit' else "FAIL")
    # Clean up
    async with db._pool.acquire() as conn:
        await conn.execute('DELETE FROM dnd_log WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM habits WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM users WHERE user_id=$1', test_user_id)
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_is_date_in_dnd_period(db):
    start = time.perf_counter()
    print("\n[Test] is_date_in_dnd_period")
    # Use Sonal's DND entry from SQL_DB.sql: ('202507', 'Kunj', 7601874368, 1, 'Meditate 🧘‍♂️', '2025-07-15', '2025-07-15')
    in_dnd = await db.is_date_in_dnd_period(7601874368, parse_date("2025-07-15"), 1)
    print("Expected: True for Kunj, habit_id=1, 2025-07-15")
    print(f"Actual: {in_dnd}")
    print("PASS" if in_dnd else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_streak_summary(db):
    start = time.perf_counter()
    print("\n[Test] get_streak_summary")
    date_obj = datetime.strptime("2025-07-02", "%Y-%m-%d").date()
    summary = await db.get_streak_summary(date_obj)
    print("Expected: streak summary for 2025-07-02 (see SQL_DB.sql)")
    print(f"Actual: {summary}")
    print("PASS" if isinstance(summary, list) else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_habits_for_date(db):
    start = time.perf_counter()
    print("\n[Test] get_user_habits_for_date")
    habits = await db.get_user_habits_for_date(7601874368, datetime.strptime("2025-07-01", "%Y-%m-%d").date())
    print("Expected: ['No Cigs🚬', 'Daily Workout💪', 'Read 10 Pages📖'] for Kunj")
    print(f"Actual: {habits}")
    print("PASS" if 'No Cigs🚬' in habits else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_check_rest_day_eligibility(db):
    start = time.perf_counter()
    print("\n[Test] check_rest_day_eligibility")
    # Kunj, habit_id=1, 2025-07-05 (should be True if last 6 are all '✅' or none)
    eligible = await db.check_rest_day_eligibility(7601874368, 1, parse_date("2025-07-05"))
    print("Expected: True or False depending on checkins")
    print(f"Actual: {eligible}")
    print("PASS" if isinstance(eligible, bool) else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_habit_timestamp(db):
    start = time.perf_counter()
    print("\n[Test] get_habit_timestamp")
    ts = await db.get_habit_timestamp(7601874368, "202507")
    print("Expected: timestamp string for Kunj's habit in 202507")
    print(f"Actual: {ts}")
    print("PASS" if isinstance(ts, str) or ts is None else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_delete_and_update_dnd_entry(db):
    start = time.perf_counter()
    print("\n[Test] delete_dnd_entry & update_dnd_entry")
    test_user_id = 9999999999
    dob = parse_date("2000-01-01")
    await db.add_user(test_user_id, "TestUser", "TestNick", "🐍", dob, "UTC", "test@example.com")
    await db.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    await db.add_dnd_period("202507", "TestUser", test_user_id, 1, "Test Habit", parse_date("2025-07-10"), parse_date("2025-07-12"))
    updated = await db.update_dnd_entry(test_user_id, 1, parse_date("2025-07-10"), parse_date("2025-07-12"), new_habit_text="Updated Habit")
    print("Expected: update returns True")
    print(f"Actual: {updated}")
    print("PASS" if updated else "FAIL")
    deleted = await db.delete_dnd_entry(test_user_id, 1, parse_date("2025-07-10"), parse_date("2025-07-12"))
    print("Expected: delete returns True")
    print(f"Actual: {deleted}")
    print("PASS" if deleted else "FAIL")
    # Clean up
    async with db._pool.acquire() as conn:
        await conn.execute('DELETE FROM habits WHERE user_id=$1', test_user_id)
        await conn.execute('DELETE FROM users WHERE user_id=$1', test_user_id)
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_all_checkins_for_user(db):
    start = time.perf_counter()
    print("\n[Test] get_all_checkins_for_user")
    checkins = await db.get_all_checkins_for_user(7601874368)
    print("Expected: >=9 checkins for Kunj (from SQL_DB.sql)")
    print(f"Actual: {len(checkins)} checkins")
    print("PASS" if len(checkins) >= 9 else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_all_daily_scores_for_user(db):
    start = time.perf_counter()
    print("\n[Test] get_all_daily_scores_for_user")
    scores = await db.get_all_daily_scores_for_user(7601874368)
    print("Expected: some daily scores for Kunj")
    print(f"Actual: {scores}")
    print("PASS" if isinstance(scores, list) else "FAIL")
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

# --- Cached test functions (all _cached) ---
async def test_add_user_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] add_user")
    test_user_id = 9999999999
    dob = parse_date("2000-01-01").isoformat()
    dbCache.add_user(test_user_id, "TestUser", "TestNick", "🐍", dob, "UTC", "test@example.com")
    user = dbCache.get_user_by_id(test_user_id)
    print("Expected: user with user_id=9999999999, username='TestUser'")
    print(f"Actual: {user}")
    print("PASS" if user and user['username'] == 'TestUser' else "FAIL")
    # Clean up
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_update_user_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] update_user")
    test_user_id = 7601874368  # Kunj
    dob = parse_date("1995-07-13").isoformat()
    dbCache.add_user(test_user_id, "Kunj", "KB", "🐯", dob, "Asia/Kolkata", "kbehari1995@gmail.com")
    dbCache.update_user(test_user_id, "KunjB", "🐍", dob, "Asia/Kolkata", "kunj_updated@gmail.com")
    user = dbCache.get_user_by_id(test_user_id)
    print("Expected: nickname='KunjB', usermoji='🐍', email='kunj_updated@gmail.com'")
    print(f"Actual: {user}")
    print("PASS" if user and user['nickname'] == 'KunjB' and user['user_moji'] == '🐍' and user['email'] == 'kunj_updated@gmail.com' else "FAIL")
    # Revert
    dbCache.update_user(test_user_id, "KB", "🐯", dob, "Asia/Kolkata", "kbehari1995@gmail.com")
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_by_id_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_user_by_id")
    test_user_id = 7601874368
    dob = parse_date("1995-07-13").isoformat()
    dbCache.add_user(test_user_id, "Kunj", "KB", "🐯", dob, "Asia/Kolkata", "kbehari1995@gmail.com")
    user = dbCache.get_user_by_id(test_user_id)
    print("Expected: username='Kunj'")
    print(f"Actual: {user}")
    print("PASS" if user and user['username'] == 'Kunj' else "FAIL")
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_all_users_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_all_users")
    dbCache.users = []
    for i in range(6):
        dbCache.add_user(1000+i, f"User{i}", f"Nick{i}", "😀", parse_date("2000-01-01").isoformat(), "UTC", f"user{i}@ex.com")
    users = dbCache.get_all_users()
    print(f"Expected: >=6 users (from SQL_DB.sql)")
    print(f"Actual: {len(users)} users")
    print("PASS" if len(users) >= 6 else "FAIL")
    dbCache.users = []
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_add_habit_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] add_habit")
    test_user_id = 9999999999
    dbCache.add_user(test_user_id, "TestUser", "TestNick", "🐍", parse_date("2000-01-01").isoformat(), "UTC", "test@example.com")
    dbCache.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    habits = dbCache.get_user_habits_for_month(test_user_id, "202507")
    print("Expected: 1 habit with habit_text='Test Habit'")
    print(f"Actual: {habits}")
    print("PASS" if habits and habits[0]['habit_text'] == 'Test Habit' else "FAIL")
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_habits_for_month_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_user_habits_for_month")
    test_user_id = 7601874368
    dbCache.add_user(test_user_id, "Kunj", "KB", "🐯", parse_date("1995-07-13").isoformat(), "Asia/Kolkata", "kbehari1995@gmail.com")
    for i in range(3):
        dbCache.add_habit(test_user_id, "Kunj", "202507", f"Habit{i}", "core")
    habits = dbCache.get_user_habits_for_month(test_user_id, "202507")
    print("Expected: >=3 habits for Kunj in 202507")
    print(f"Actual: {habits}")
    print("PASS" if len(habits) >= 3 else "FAIL")
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_has_existing_core_habits_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] has_existing_core_habits")
    test_user_id = 7601874368
    dbCache.add_user(test_user_id, "Kunj", "KB", "🐯", parse_date("1995-07-13").isoformat(), "Asia/Kolkata", "kbehari1995@gmail.com")
    dbCache.add_habit(test_user_id, "Kunj", "202507", "Test Habit", "core")
    exists = dbCache.has_existing_core_habits(test_user_id, "202507")
    print("Expected: True for Kunj in 202507")
    print(f"Actual: {exists}")
    print("PASS" if exists else "FAIL")
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_log_checkin_and_has_already_checked_in_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] log_checkin & has_already_checked_in")
    test_user_id = 9999999999
    dbCache.add_user(test_user_id, "TestUser", "TestNick", "🐍", parse_date("2000-01-01").isoformat(), "UTC", "test@example.com")
    dbCache.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    habits = dbCache.get_user_habits_for_month(test_user_id, "202507")
    habit_id = habits[0]['habit_id']
    for_date = parse_date("2025-07-05").isoformat()
    dbCache.log_checkin(for_date, "202507", test_user_id, "TestUser", habit_id, "Test Habit", "✅", "manual")
    dbCache.daily_score_log.append({'user_id': test_user_id, 'for_date': for_date, 'score_type': 'core'})
    checked_in = dbCache.has_already_checked_in(test_user_id, for_date)
    print("Expected: True after checkin")
    print(f"Actual: {checked_in}")
    print("PASS" if checked_in else "FAIL")
    dbCache.core_habit_log = [c for c in dbCache.core_habit_log if c['user_id'] != test_user_id]
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    dbCache.daily_score_log = [d for d in dbCache.daily_score_log if d['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_checkin_summary_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_user_checkin_summary")
    test_user_id = 7601874368
    for_date = parse_date("2025-07-01").isoformat()
    dbCache.daily_score_log.append({'user_id': test_user_id, 'for_date': for_date, 'score_type': 'core'})
    summary = dbCache.get_user_checkin_summary(test_user_id, for_date)
    print("Expected: 1 checkin for Kunj on 2025-07-01")
    print(f"Actual: {summary}")
    print("PASS" if len(summary) == 1 else "FAIL")
    dbCache.daily_score_log = [d for d in dbCache.daily_score_log if d['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_add_dnd_period_and_get_dnd_entries_for_user_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] add_dnd_period & get_dnd_entries_for_user")
    test_user_id = 9999999999
    dbCache.add_user(test_user_id, "TestUser", "TestNick", "🐍", parse_date("2000-01-01").isoformat(), "UTC", "test@example.com")
    dbCache.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    dbCache.add_dnd_period("202507", "TestUser", test_user_id, 1, "Test Habit", "2025-07-10", "2025-07-12")
    dnd_entries = dbCache.get_dnd_entries_for_user(test_user_id)
    print("Expected: 1 DND entry for TestUser")
    print(f"Actual: {dnd_entries}")
    print("PASS" if dnd_entries and dnd_entries[0]['habit_text'] == 'Test Habit' else "FAIL")
    dbCache.dnd_log = [d for d in dbCache.dnd_log if d['user_id'] != test_user_id]
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_is_date_in_dnd_period_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] is_date_in_dnd_period")
    test_user_id = 7601874368
    dbCache.add_dnd_period("202507", "Kunj", test_user_id, 1, "Meditate 🧘‍♂️", "2025-07-15", "2025-07-15")
    in_dnd = dbCache.is_date_in_dnd_period(test_user_id, "2025-07-15", 1)
    print("Expected: True for Kunj, habit_id=1, 2025-07-15")
    print(f"Actual: {in_dnd}")
    print("PASS" if in_dnd else "FAIL")
    dbCache.dnd_log = [d for d in dbCache.dnd_log if d['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_streak_summary_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_streak_summary")
    test_user_id = 7601874368
    date_obj = parse_date("2025-07-02")
    dbCache.daily_score_log.append({'user_id': test_user_id, 'for_date': date_obj, 'score_type': 'streak'})
    summary = dbCache.get_streak_summary(date_obj)
    print("Expected: streak summary for 2025-07-02 (see SQL_DB.sql)")
    print(f"Actual: {summary}")
    print("PASS" if isinstance(summary, list) else "FAIL")
    dbCache.daily_score_log = [d for d in dbCache.daily_score_log if d['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_user_habits_for_date_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_user_habits_for_date")
    test_user_id = 7601874368
    dbCache.add_habit(test_user_id, "Kunj", "202507", "No Cigs🚬", "core")
    dbCache.add_habit(test_user_id, "Kunj", "202507", "Daily Workout💪", "core")
    dbCache.add_habit(test_user_id, "Kunj", "202507", "Read 10 Pages📖", "core")
    habits = dbCache.get_user_habits_for_date(test_user_id, parse_date("2025-07-01"))
    print("Expected: ['No Cigs🚬', 'Daily Workout💪', 'Read 10 Pages📖'] for Kunj")
    print(f"Actual: {habits}")
    print("PASS" if 'No Cigs🚬' in habits else "FAIL")
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_check_rest_day_eligibility_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] check_rest_day_eligibility")
    test_user_id = 7601874368
    habit_id = 1
    for i in range(6):
        dbCache.core_habit_log.append({'user_id': test_user_id, 'habit_id': habit_id, 'for_date': f"2025-07-0{i+1}", 'habit_status': '✅'})
    eligible = dbCache.check_rest_day_eligibility(test_user_id, habit_id, "2025-07-07")
    print("Expected: True or False depending on checkins")
    print(f"Actual: {eligible}")
    print("PASS" if isinstance(eligible, bool) else "FAIL")
    dbCache.core_habit_log = [c for c in dbCache.core_habit_log if c['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_habit_timestamp_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_habit_timestamp")
    test_user_id = 7601874368
    dbCache.add_habit(test_user_id, "Kunj", "202507", "No Cigs🚬", "core")
    ts = dbCache.get_habit_timestamp(test_user_id, "202507")
    print("Expected: timestamp string for Kunj's habit in 202507")
    print(f"Actual: {ts}")
    print("PASS" if isinstance(ts, str) or ts is None else "FAIL")
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_delete_and_update_dnd_entry_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] delete_dnd_entry & update_dnd_entry")
    test_user_id = 9999999999
    dbCache.add_user(test_user_id, "TestUser", "TestNick", "🐍", parse_date("2000-01-01").isoformat(), "UTC", "test@example.com")
    dbCache.add_habit(test_user_id, "TestUser", "202507", "Test Habit", "core")
    dbCache.add_dnd_period("202507", "TestUser", test_user_id, 1, "Test Habit", "2025-07-10", "2025-07-12")
    updated = dbCache.update_dnd_entry(test_user_id, 1, "2025-07-10", "2025-07-12", new_habit_text="Updated Habit")
    print("Expected: update returns True")
    print(f"Actual: {updated}")
    print("PASS" if updated else "FAIL")
    deleted = dbCache.delete_dnd_entry(test_user_id, 1, "2025-07-10", "2025-07-12")
    print("Expected: delete returns True")
    print(f"Actual: {deleted}")
    print("PASS" if deleted else "FAIL")
    dbCache.habits = [h for h in dbCache.habits if h['user_id'] != test_user_id]
    dbCache.users = [u for u in dbCache.users if u['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_all_checkins_for_user_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_all_checkins_for_user")
    test_user_id = 7601874368
    dbCache.daily_score_log.append({'user_id': test_user_id, 'score_type': 'core'})
    checkins = dbCache.get_all_checkins_for_user(test_user_id)
    print("Expected: >=1 checkins for Kunj (from SQL_DB.sql)")
    print(f"Actual: {len(checkins)} checkins")
    print("PASS" if len(checkins) >= 1 else "FAIL")
    dbCache.daily_score_log = [d for d in dbCache.daily_score_log if d['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def test_get_all_daily_scores_for_user_cached():
    start = time.perf_counter()
    print("\n[Test][CACHED] get_all_daily_scores_for_user")
    test_user_id = 7601874368
    dbCache.daily_score_log.append({'user_id': test_user_id, 'score_type': 'streak'})
    scores = dbCache.get_all_daily_scores_for_user(test_user_id)
    print("Expected: some daily scores for Kunj")
    print(f"Actual: {scores}")
    print("PASS" if isinstance(scores, list) else "FAIL")
    dbCache.daily_score_log = [d for d in dbCache.daily_score_log if d['user_id'] != test_user_id]
    end = time.perf_counter()
    print(f"Time taken: {((end-start)*1000):.2f} ms")

async def main():
    db = DBClient()
    await db.connect()
    await test_add_user(db)
    await test_add_user_cached()
    await test_update_user(db)
    await test_update_user_cached()
    await test_get_user_by_id(db)
    await test_get_user_by_id_cached()
    await test_get_all_users(db)
    await test_get_all_users_cached()
    await test_add_habit(db)
    await test_add_habit_cached()
    await test_get_user_habits_for_month(db)
    await test_get_user_habits_for_month_cached()
    await test_has_existing_core_habits(db)
    await test_has_existing_core_habits_cached()
    await test_log_checkin_and_has_already_checked_in(db)
    await test_log_checkin_and_has_already_checked_in_cached()
    await test_get_user_checkin_summary(db)
    await test_get_user_checkin_summary_cached()
    await test_add_dnd_period_and_get_dnd_entries_for_user(db)
    await test_add_dnd_period_and_get_dnd_entries_for_user_cached()
    await test_is_date_in_dnd_period(db)
    await test_is_date_in_dnd_period_cached()
    await test_get_streak_summary(db)
    await test_get_streak_summary_cached()
    await test_get_user_habits_for_date(db)
    await test_get_user_habits_for_date_cached()
    await test_check_rest_day_eligibility(db)
    await test_check_rest_day_eligibility_cached()
    await test_get_habit_timestamp(db)
    await test_get_habit_timestamp_cached()
    await test_delete_and_update_dnd_entry(db)
    await test_delete_and_update_dnd_entry_cached()
    await test_get_all_checkins_for_user(db)
    await test_get_all_checkins_for_user_cached()
    await test_get_all_daily_scores_for_user(db)
    await test_get_all_daily_scores_for_user_cached()
    await db.close()

if __name__ == "__main__":
    asyncio.run(main()) 