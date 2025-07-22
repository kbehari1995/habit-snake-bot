import os
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
import threading
from bot.utils.db import DBClient  # <-- Add this import
import asyncio

class DbCacheError(Exception):
    pass

class DbCache:
    _instance = None
    _initialized = False
    _lock = threading.RLock()

    @classmethod
    def refresh_cache(cls):
        print("DEBUG: Acquiring lock in refresh_cache")
        with cls._lock:
            print("DEBUG: Acquired lock in refresh_cache")
            cls._instance = None
            cls._initialized = False
            return cls()

    def __new__(cls, *args, **kwargs):
        print("DEBUG: Acquiring lock in __new__")
        with cls._lock:
            print("DEBUG: Acquired lock in __new__")
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self.__class__._initialized:
            return
        # In-memory cache for each table
        self.users = []  # List[dict]
        self.habits = []  # List[dict]
        self.core_habit_log = []  # List[dict]
        self.dnd_log = []  # List[dict]
        self.daily_score_log = []  # List[dict]
        self._load_all()
        self.__class__._initialized = True

    def _load_all(self):
        # Load all tables from the database into the cache
        db_client = DBClient()
        loop = asyncio.get_event_loop()
        # Connect to DB
        loop.run_until_complete(db_client.connect())
        # Fetch all users
        self.users = loop.run_until_complete(db_client.get_all_users())
        # Fetch all habits
        query = 'SELECT * FROM habits'
        async def fetch_all_habits():
            
            async with db_client._pool.acquire() as conn:
                rows = await conn.fetch(query)
                return [dict(r) for r in rows]
        self.habits = loop.run_until_complete(fetch_all_habits())
        # Fetch all core habit logs
        query = 'SELECT * FROM core_habit_log'
        async def fetch_all_core_habit_log():
            async with db_client._pool.acquire() as conn:
                rows = await conn.fetch(query)
                return [dict(r) for r in rows]
        self.core_habit_log = loop.run_until_complete(fetch_all_core_habit_log())
        # Fetch all dnd logs
        query = 'SELECT * FROM dnd_log'
        async def fetch_all_dnd_log():
            async with db_client._pool.acquire() as conn:
                rows = await conn.fetch(query)
                print("Ye mila hai",rows)
                return [dict(r) for r in rows]
        self.dnd_log = loop.run_until_complete(fetch_all_dnd_log())
        # Fetch all daily score logs
        query = 'SELECT * FROM daily_score_log'
        async def fetch_all_daily_score_log():
            async with db_client._pool.acquire() as conn:
                rows = await conn.fetch(query)
                return [dict(r) for r in rows]
        self.daily_score_log = loop.run_until_complete(fetch_all_daily_score_log())
        # Optionally close DB connection
        loop.run_until_complete(db_client.close())

    # USERS
    def add_user(self, user_id: int, username: str, nickname: str, user_moji: str, dob: str, timezone: str, email: str, user_status: str = 'active'):
        user = {
            'user_id': user_id,
            'username': username,
            'nickname': nickname,
            'user_moji': user_moji,
            'dob': dob,
            'timezone': timezone,
            'email': email,
            'user_status': user_status,
            'last_born_on': datetime.now().date(),
            'last_died_on': None,
            'created_at': datetime.now()
        }
        self.users.append(user)

    async def add_user_to_db(self, user_id: int, username: str, nickname: str, user_moji: str, dob: str, timezone: str, email: str, user_status: str = 'active'):
        """Insert a new user directly into the database using DBClient."""
        db_client = DBClient()
        await db_client.connect()
        await db_client.add_user(user_id, username, nickname, user_moji, dob, timezone, email, user_status)
        # await db_client.close()  # Only if you want to close after every op

    def update_user(self, user_id: int, nickname: str, user_moji: str, dob: str, timezone: str, email: str):
        for user in self.users:
            if user['user_id'] == user_id:
                user['nickname'] = nickname
                user['user_moji'] = user_moji
                user['dob'] = dob
                user['timezone'] = timezone
                user['email'] = email
                user['last_born_on'] = datetime.now().date()
                return True
        return False

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        for user in self.users:
            if user['user_id'] == user_id:
                return user
        return None

    def get_all_users(self) -> List[dict]:
        return list(self.users)

    # HABITS
    def add_habit_to_cache(self, user_id: int, username: str, year_month: str, habit_text: str, habit_type: str):
        """
        Add a habit to the in-memory cache only (does not persist to DB).
        """
        habit = {
            'habit_id': len(self.habits) + 1,
            'user_id': user_id,
            'username': username,
            'year_month': year_month,
            'habit_text': habit_text,
            'habit_type': habit_type,
            'created_at': datetime.now()
        }
        self.habits.append(habit)

    async def add_habit_to_db(self, user_id: int, username: str, year_month: str, habit_text: str, habit_type: str):
        """
        Add a habit directly to the database using DBClient.
        """
        from bot.utils.db import DBClient
        db_client = DBClient()
        await db_client.connect()
        await db_client.add_habit(user_id, username, year_month, habit_text, habit_type)
       
    
    def get_user_habits_for_month(self, user_id: int, year_month: str) -> List[dict]:
        year_month = year_month.strip()
        return [h for h in self.habits if int(h['user_id']) == int(user_id) and h['year_month'].strip() == year_month]

    def has_existing_core_habits(self, user_id: int, year_month: str) -> bool:
        return any(h for h in self.habits if h['user_id'] == user_id and h['year_month'] == year_month and h['habit_type'] == 'core')

    async def add_habits_to_db(self, user_id: int, username: str, year_month: str, habit_texts: list, habit_type: str):
        """
        Batch insert multiple habits directly to the database using DBClient.
        """
        from bot.utils.db import DBClient
        db_client = DBClient()
        await db_client.connect()
        habits = [
            {
                'user_id': user_id,
                'username': username,
                'year_month': year_month,
                'habit_text': habit_text,
                'habit_type': habit_type
            }
            for habit_text in habit_texts
        ]
        await db_client.add_habits(habits)

    def has_already_checked_in(self, user_id: int, for_date: str) -> bool:
        for row in self.daily_score_log:
            if (
                row['user_id'] == user_id and
                str(row['for_date']) == for_date and
                row['score_type'].strip() == 'core'
            ):
                return True
        return False

    def get_user_checkin_summary(self, user_id: int, for_date: str) -> List[dict]:
        return [row for row in self.daily_score_log if row['user_id'] == user_id and str(row['for_date']) == for_date and row['score_type'] == 'core']

    def log_checkin_to_cache(self, for_date: str, year_month: str, user_id: int, username: str, habit_id: int, habit_text: str, habit_status: str, marked_by: str):
        """
        Add a check-in entry to the in-memory cache only (does not persist to DB).
        """
        entry = {
            'core_log_id': len(self.core_habit_log) + 1,
            'for_date': for_date,
            'year_month': year_month,
            'user_id': user_id,
            'username': username,
            'habit_id': habit_id,
            'habit_text': habit_text,
            'habit_status': habit_status,
            'marked_by': marked_by,
            'created_at': datetime.now()
        }
        self.core_habit_log.append(entry)

    async def log_checkin_to_db(self, checkins: list):
        """
        Batch insert m  tiple check-in entries directly to the database using DBClient.
        Each check-in dict should contain: for_date, year_month, user_id, username, habit_id, habit_text, habit_status, marked_by
        """
        from bot.utils.db import DBClient
        db_client = DBClient()
        await db_client.connect()
        await db_client.add_checkins(checkins)

    # DND
    def add_dnd_period_to_cache(self, year_month: str, username: str, user_id: int, habit_id: int, habit_text: str, start_date: str, end_date: str):
        """
        Add a DND period to the in-memory cache only (does not persist to DB).
        Returns the dnd_log_id of the new entry.
        """
        entry = {
            'dnd_log_id': len(self.dnd_log) + 1,
            'year_month': year_month,
            'username': username,
            'user_id': user_id,
            'habit_id': habit_id,
            'habit_text': habit_text,
            'start_date': datetime.strptime(start_date, "%Y-%m-%d").date(),
            'end_date': datetime.strptime(end_date, "%Y-%m-%d").date(),
            'created_at': datetime.now()
        }
        self.dnd_log.append(entry)
        return entry['dnd_log_id']

    async def add_dnd_period_to_db(self, year_month: str, username: str, user_id: int, habit_id: int, habit_text: str, start_date: str, end_date: str):
        """
        Add a DND period directly to the database using DBClient.
        """
        from bot.utils.db import DBClient
        db_client = DBClient()
        await db_client.connect()
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        dnd_log_id = await db_client.add_dnd_period(year_month, username, user_id, habit_id, habit_text, start_dt, end_dt)
        return dnd_log_id

    def get_dnd_entries_for_user(self, user_id: int) -> List[dict]:
        return [row for row in self.dnd_log if row['user_id'] == user_id]

    def is_date_in_dnd_period(self, user_id: int, check_date: str, habit_id: int) -> bool:
        check_dt = datetime.strptime(check_date, "%Y-%m-%d").date()
        for row in self.dnd_log:
            if row['user_id'] == user_id and row['habit_id'] == habit_id:
                # Handle both str and date for start_date and end_date
                start_dt = row['start_date'] if isinstance(row['start_date'], date) else datetime.strptime(row['start_date'], "%Y-%m-%d").date()
                end_dt = row['end_date'] if isinstance(row['end_date'], date) else datetime.strptime(row['end_date'], "%Y-%m-%d").date()
                if start_dt <= check_dt <= end_dt:
                    return True
        return False

    # DAILY SCORE LOG
    def get_streak_summary(self, for_date: date) -> List[dict]:
        return [row for row in self.daily_score_log if row['for_date'] == for_date and row['score_type'] == 'streak']

    # Utility: get habits for a user for a date (month)
    def get_user_habits_for_date(self, user_id: int, date_obj: date) -> List[str]:
        year_month = date_obj.strftime('%Y%m')
        return [h for h in self.habits if h['user_id'] == user_id and h['year_month'] == year_month]

    # Utility: check rest day eligibility (last 6 check-ins for a habit are all '✅')
    def check_rest_day_eligibility(self, user_id: int, habit_id: int, check_date: str) -> bool:
        # Get last 6 check-ins for this habit before check_date
        checkins = [row for row in self.core_habit_log if row['user_id'] == user_id and row['habit_id'] == habit_id and str(row['for_date']) < check_date]
        checkins.sort(key=lambda x: str(x['for_date']), reverse=True)
        last_six = checkins[:6]
        return len(last_six) == 6 and all(r['habit_status'] == '✅' for r in last_six)

    # Utility: get habit timestamp (created_at) for a user's habit in a month
    def get_habit_timestamp(self, user_id: int, year_month: str) -> Optional[str]:
        habits = [h for h in self.habits if h['user_id'] == user_id and h['year_month'] == year_month]
        if not habits:
            return None
        latest = max(habits, key=lambda h: h['created_at'])
        return latest['created_at'].isoformat() if latest else None

    # Utility: delete DND entry
    def delete_dnd_entry_from_cache(self, dnd_log_id: int) -> bool:
        """
        Delete a DND entry from the in-memory cache only.
        """
        for i, row in enumerate(self.dnd_log):
            if row['dnd_log_id'] == dnd_log_id:
                del self.dnd_log[i]
                return True
        return False

    async def delete_dnd_entry_in_db(self, dnd_log_id: int) -> bool:
        """
        Delete a DND entry directly from the database using DBClient.
        """
        from bot.utils.db import DBClient
        db_client = DBClient()
        await db_client.connect()
        result = await db_client.delete_dnd_entry(dnd_log_id)
        # await db_client.close()
        return result

    # Utility: update DND entry
    def update_dnd_entry_to_cache(self, dnd_log_id: int, new_habit_text: Optional[str] = None, new_start_date: Optional[str] = None, new_end_date: Optional[str] = None) -> bool:
        """
        Update a DND entry in the in-memory cache only.
        """
        for row in self.dnd_log:
            if row['dnd_log_id'] == dnd_log_id:
                if new_habit_text:
                    row['habit_text'] = new_habit_text
                if new_start_date:
                    row['start_date'] = datetime.strptime(new_start_date, "%Y-%m-%d").date()
                if new_end_date:
                    row['end_date'] = datetime.strptime(new_end_date, "%Y-%m-%d").date()
                return True
        return False

    async def update_dnd_entry_in_db(self, dnd_log_id: int, new_habit_text: Optional[str] = None, new_start_date: Optional[str] = None, new_end_date: Optional[str] = None) -> bool:
        """
        Update a DND entry directly in the database using DBClient.
        """
        from bot.utils.db import DBClient
        db_client = DBClient()
        await db_client.connect()
        result = await db_client.update_dnd_entry(dnd_log_id, new_habit_text, new_start_date, new_end_date)
        # await db_client.close()
        return result

    # Utility: get all check-ins for a user
    def get_all_checkins_for_user(self, user_id: int) -> List[dict]:
        return [row for row in self.daily_score_log if row['user_id'] == user_id and row['score_type'] == 'core']

    # Utility: get all daily scores for a user
    def get_all_daily_scores_for_user(self, user_id: int) -> List[dict]:
        return [row for row in self.daily_score_log if row['user_id'] == user_id and row['score_type'] == 'streak']

# Usage example (in your bot):
dbCache = DbCache()
# dbCache.add_user(...)
# dbCache.add_habit(...)
# ... 