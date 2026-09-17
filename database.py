import aiosqlite
import json
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                file_type TEXT NOT NULL,
                caption TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT UNIQUE NOT NULL,
                title TEXT,
                invite_link TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS banner (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                file_id TEXT,
                file_type TEXT,
                caption TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduled (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                file_id TEXT,
                file_type TEXT,
                caption TEXT,
                run_at TEXT NOT NULL,
                sent INTEGER DEFAULT 0,
                retries INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fsm_state (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                data TEXT DEFAULT '{}'
            )
        """)
        await db.commit()


# ===== کاربران =====
async def add_user(user_id, username, first_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def get_users_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            return (await cur.fetchone())[0]


# ===== فایل‌ها =====
async def add_file(file_id, file_type, caption):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO files (file_id, file_type, caption) VALUES (?, ?, ?)",
            (file_id, file_type, caption)
        )
        await db.commit()
        return cur.lastrowid


async def get_all_files():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, file_id, file_type, caption FROM files ORDER BY id DESC"
        ) as cur:
            return await cur.fetchall()


async def get_file(file_id_db):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id, file_type, caption FROM files WHERE id = ?",
            (file_id_db,)
        ) as cur:
            return await cur.fetchone()


async def update_caption(file_id_db, new_caption):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE files SET caption = ? WHERE id = ?",
            (new_caption, file_id_db)
        )
        await db.commit()


async def delete_file(file_id_db):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM files WHERE id = ?", (file_id_db,))
        await db.commit()


# ===== کانال‌ها =====
async def add_channel(chat_id, title, invite_link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO channels (chat_id, title, invite_link) VALUES (?, ?, ?)",
            (chat_id, title, invite_link)
        )
        await db.commit()


async def get_all_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT id, chat_id, title, invite_link FROM channels"
        ) as cur:
            return await cur.fetchall()


async def delete_channel(channel_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await db.commit()


# ===== بنر =====
async def set_banner(file_id, file_type, caption):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO banner (id, file_id, file_type, caption) VALUES (1, ?, ?, ?)",
            (file_id, file_type, caption)
        )
        await db.commit()


async def get_banner():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT file_id, file_type, caption FROM banner WHERE id = 1"
        ) as cur:
            return await cur.fetchone()


# ===== زمان‌بندی =====
async def add_scheduled(chat_id, file_id, file_type, caption, run_at):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO scheduled 
               (chat_id, file_id, file_type, caption, run_at) 
               VALUES (?, ?, ?, ?, ?)""",
            (str(chat_id), file_id, file_type, caption, run_at)
        )
        await db.commit()
        return cur.lastrowid


async def get_pending_scheduled():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT id, chat_id, file_id, file_type, caption, run_at 
               FROM scheduled 
               WHERE sent = 0 AND retries < 3"""
        ) as cur:
            return await cur.fetchall()


async def get_all_scheduled():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT id, chat_id, file_id, file_type, caption, run_at, sent 
               FROM scheduled 
               ORDER BY run_at ASC"""
        ) as cur:
            return await cur.fetchall()


async def mark_sent(schedule_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduled SET sent = 1 WHERE id = ?",
            (schedule_id,)
        )
        await db.commit()


async def increment_retry(schedule_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduled SET retries = retries + 1 WHERE id = ?",
            (schedule_id,)
        )
        await db.commit()


async def delete_scheduled(schedule_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scheduled WHERE id = ?", (schedule_id,))
        await db.commit()


# ===== FSM =====
async def set_fsm(user_id, state, data=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO fsm_state (user_id, state, data) VALUES (?, ?, ?)",
            (user_id, state, json.dumps(data or {}))
        )
        await db.commit()


async def get_fsm(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT state, data FROM fsm_state WHERE user_id = ?",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            if row:
                return row[0], json.loads(row[1])
            return None, {}


async def clear_fsm(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM fsm_state WHERE user_id = ?", (user_id,))
        await db.commit()
