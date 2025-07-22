import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, Tuple

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

class DBError(Exception):
    pass

class DBClient:
    def __init__(self):
        self._pool = None

    async def connect(self):
        if not self._pool:
            self._pool = await asyncpg.create_pool(DATABASE_URL)

    async def close(self):
        if self._pool:
            await self._pool.close()
            self._pool = None

    # USERS
    async def add_user(self, user_id: int, username: str, nickname: str, user_moji: str, dob: str, timezone: str, email: str, user_status: str = 'active'):
        """Insert a new user."""
        query = '''
        INSERT INTO users (user_id, username, nickname, user_moji, dob, timezone, email, user_status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (user_id) DO NOTHING;
        '''
        async with self._pool.acquire() as conn:
            await conn.execute(query, user_id, username, nickname, user_moji, dob, timezone, email, user_status)

    async def update_user(self, user_id: int, nickname: str, user_moji: str, dob: str, timezone: str, email: str):
        """Update user fields by user_id."""
        query = '''
        UPDATE users SET nickname=$2, user_moji=$3, dob=$4, timezone=$5, email=$6, last_born_on=NOW()
        WHERE user_id=$1
        '''
        async with self._pool.acquire() as conn:
            await conn.execute(query, user_id, nickname, user_moji, dob, timezone, email)

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        query = 'SELECT * FROM users WHERE user_id=$1'
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None

    async def get_all_users(self) -> List[dict]:
        query = 'SELECT * FROM users'
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(r) for r in rows]

    # HABITS
    async def add_habit(self, user_id: int, username: str, year_month: str, habit_text: str, habit_type: str):
        query = '''
        INSERT INTO habits (user_id, username, year_month, habit_text, habit_type)
        VALUES ($1, $2, $3, $4, $5)
        '''
        async with self._pool.acquire() as conn:
            await conn.execute(query, user_id, username, year_month, habit_text, habit_type)

    async def add_habits(self, habits: list):
        """
        Batch insert multiple habits. Each habit is a dict with keys: user_id, username, year_month, habit_text, habit_type
        """
        if not habits:
            return
        query = '''
        INSERT INTO habits (user_id, username, year_month, habit_text, habit_type)
        VALUES ($1, $2, $3, $4, $5)
        '''
        values = [
            (
                habit['user_id'],
                habit['username'],
                habit['year_month'],
                habit['habit_text'],
                habit['habit_type']
            )
            for habit in habits
        ]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, values)

    async def get_user_habits_for_month(self, user_id: int, year_month: str) -> List[dict]:
        query = '''
        SELECT * FROM habits WHERE user_id=$1 AND year_month=$2
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, year_month)
            return [dict(r) for r in rows]

    async def has_existing_core_habits(self, user_id: int, year_month: str) -> bool:
        query = '''
        SELECT 1 FROM habits WHERE user_id=$1 AND year_month=$2 AND habit_type='core' LIMIT 1
        '''
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, year_month)
            return bool(row)

    # CHECK-INS (core_habit_log)
    async def log_checkin(self, for_date: str, year_month: str, user_id: int, username: str, habit_id: int, habit_text: str, habit_status: str, marked_by: str):
        query = '''
        INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        '''
        async with self._pool.acquire() as conn:
            await conn.execute(query, for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by)

   #has_already_checked_in is true if in daily score log scoretype is core and a row is present for the userid for that date
    async def has_already_checked_in(self, user_id: int, for_date: str) -> bool:
        query = '''
        SELECT 1 FROM daily_score_log WHERE user_id=$1 AND for_date=$2 AND score_type='core' LIMIT 1
        '''
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, for_date)
            return bool(row)

    async def get_user_checkin_summary(self, user_id: int, for_date: str) -> List[dict]:
        query = '''
         SELECT * FROM daily_score_log WHERE user_id=$1 AND for_date=$2 AND score_type='core' LIMIT 1
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, for_date)
            return [dict(r) for r in rows]

    # DND
    async def add_dnd_period(self, year_month: str, username: str, user_id: int, habit_id: int, habit_text: str, start_date: str, end_date: str):
        query = '''
            INSERT INTO dnd_log (year_month, username, user_id, habit_id, habit_text, start_date, end_date)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING dnd_log_id
        '''
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, year_month, username, user_id, habit_id, habit_text, start_date, end_date)
        return row['dnd_log_id'] if row else None

    async def get_dnd_entries_for_user(self, user_id: int) -> List[dict]:
        query = 'SELECT * FROM dnd_log WHERE user_id=$1'
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    async def is_date_in_dnd_period(self, user_id: int, check_date: str, habit_id: int) -> bool:
        query = '''
        SELECT 1 FROM dnd_log WHERE user_id=$1 AND habit_id=$2 AND start_date <= $3 AND end_date >= $3 LIMIT 1
        '''
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, habit_id, check_date)
            return bool(row)

    # DAILY SCORE LOG
    async def get_streak_summary(self, for_date: date) -> List[dict]:
        """Get all streak summary rows for a given date (expects a datetime.date object)."""
        query = '''
        SELECT * FROM daily_score_log WHERE for_date=$1 AND score_type='streak'
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, for_date)
            return [dict(r) for r in rows]

   #  async def log_streak_row(self, for_date: str, user_id: int, username: str, log_txt_json: dict, score: int, score_type: str):
   #      query = '''
   #      INSERT INTO daily_score_log (for_date, user_id, username, log_txt_json, score, score_type)
   #      VALUES ($1, $2, $3, $4, $5, $6)
   #      '''
   #      async with self._pool.acquire() as conn:
   #          await conn.execute(query, for_date, user_id, username, log_txt_json, score, score_type)

    # Utility: get habits for a user for a date (month)
    async def get_user_habits_for_date(self, user_id: int, date_obj: date) -> List[str]:
        year_month = date_obj.strftime('%Y%m')
        query = '''
        SELECT habit_text FROM habits WHERE user_id=$1 AND year_month=$2
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, year_month)
            return [r['habit_text'] for r in rows]

    # Utility: check rest day eligibility (last 6 check-ins for a habit are all '✅')
    async def check_rest_day_eligibility(self, user_id: int, habit_id: int, check_date: str) -> bool:
        query = '''
        SELECT habit_status FROM core_habit_log
        WHERE user_id=$1 AND habit_id=$2 AND for_date < $3
        ORDER BY for_date DESC LIMIT 6
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id, habit_id, check_date)
            return all(r['habit_status'] == '✅' for r in rows) if rows else True

    # Utility: get habit timestamp (created_at) for a user's habit in a month
    async def get_habit_timestamp(self, user_id: int, year_month: str) -> Optional[str]:
        query = '''
        SELECT created_at FROM habits WHERE user_id=$1 AND year_month=$2 ORDER BY created_at DESC LIMIT 1
        '''
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, year_month)
            return row['created_at'].isoformat() if row else None

    # Utility: delete DND entry
    async def delete_dnd_entry(self, dnd_log_id: int) -> bool:
        query = 'DELETE FROM dnd_log WHERE dnd_log_id=$1'
        async with self._pool.acquire() as conn:
            result = await conn.execute(query, dnd_log_id)
            return result[-1] == '1'

    # Utility: update DND entry
    async def update_dnd_entry(self, dnd_log_id: int, new_habit_text: Optional[str] = None, new_start_date: Optional[str] = None, new_end_date: Optional[str] = None) -> bool:
        from datetime import datetime, date
        set_clauses = []
        params = []
        if new_habit_text is not None:
            set_clauses.append('habit_text=$' + str(len(params)+2))
            params.append(new_habit_text)
        if new_start_date is not None:
            if isinstance(new_start_date, str):
                new_start_date = datetime.strptime(new_start_date, "%Y-%m-%d").date()
            set_clauses.append('start_date=$' + str(len(params)+2))
            params.append(new_start_date)
        if new_end_date is not None:
            if isinstance(new_end_date, str):
                new_end_date = datetime.strptime(new_end_date, "%Y-%m-%d").date()
            set_clauses.append('end_date=$' + str(len(params)+2))
            params.append(new_end_date)
        if not set_clauses:
            return False
        set_clause = ', '.join(set_clauses)
        query = f'UPDATE dnd_log SET {set_clause} WHERE dnd_log_id=$1'
        async with self._pool.acquire() as conn:
            result = await conn.execute(query, dnd_log_id, *params)
            return result[-1] == '1'

    # Utility: get all check-ins for a user
    async def get_all_checkins_for_user(self, user_id: int) -> List[dict]:
        query = '''SELECT * FROM daily_score_log WHERE user_id=$1 and score_type='core'
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(r) for r in rows]

    # Utility: get all daily scores for a user
    async def get_all_daily_scores_for_user(self, user_id: int) -> List[dict]:
        query = '''SELECT * FROM daily_score_log WHERE user_id=$1 and score_type='streak'
        '''
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, user_id)
            return [dict(r) for r in rows]

    async def add_checkins(self, checkins: list):
        """
        Batch insert multiple check-ins. Each check-in is a dict with keys: for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by
        """
        if not checkins:
            return
        query = '''
        INSERT INTO core_habit_log (for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        '''
        values = [
            (
                c['for_date'],
                c['year_month'],
                c['user_id'],
                c['username'],
                c['habit_id'],
                c['habit_text'],
                c['habit_status'],
                c['marked_by']
            )
            for c in checkins
        ]
        async with self._pool.acquire() as conn:
            await conn.executemany(query, values)

# Usage example (in your bot):
# db = DBClient()
# await db.connect()
# await db.add_user(...)
# ...
# await db.close() 