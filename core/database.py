import sqlite3
import logging
from datetime import datetime
from models import User, SocialAccount, Post

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path="database.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                platform TEXT,
                platform_id TEXT,
                username TEXT,
                access_token TEXT,
                created_at TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                platforms TEXT,
                media_files TEXT,
                status TEXT,
                published_at TIMESTAMP,
                created_at TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    def add_user(self, user: User) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                (user.telegram_id, user.username, user.first_name, user.last_name,
                 user.created_at.isoformat() if user.created_at else datetime.now().isoformat())
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Add user error: {e}")
            return False

    def add_social_account(self, account: SocialAccount) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO social_accounts 
                (user_id, platform, platform_id, username, access_token, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                account.user_id, account.platform, account.platform_id,
                account.username, account.access_token,
                account.created_at.isoformat() if account.created_at else datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Add account error: {e}")
            return False

    def get_user_accounts(self, user_id: int, platform: str = None):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if platform:
                cursor.execute(
                    "SELECT * FROM social_accounts WHERE user_id = ? AND platform = ?",
                    (user_id, platform)
                )
            else:
                cursor.execute(
                    "SELECT * FROM social_accounts WHERE user_id = ?",
                    (user_id,)
                )

            rows = cursor.fetchall()
            conn.close()

            accounts = []
            for row in rows:
                accounts.append(SocialAccount(
                    user_id=row['user_id'],
                    platform=row['platform'],
                    platform_id=row['platform_id'],
                    username=row['username'],
                    access_token=row['access_token']
                ))
            return accounts
        except Exception as e:
            logger.error(f"Get accounts error: {e}")
            return []

    def add_post(self, post: Post):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            platforms = ','.join(post.platforms) if post.platforms else ''
            media = ','.join(post.media_files) if post.media_files else ''

            cursor.execute("""
                INSERT INTO posts 
                (user_id, text, platforms, media_files, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                post.user_id, post.text, platforms, media,
                post.status, datetime.now().isoformat()
            ))

            post_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return post_id
        except Exception as e:
            logger.error(f"Add post error: {e}")
            return -1

    def update_post_status(self, post_id: int, status: str, published_at: datetime = None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            if published_at:
                cursor.execute(
                    "UPDATE posts SET status = ?, published_at = ? WHERE id = ?",
                    (status, published_at.isoformat(), post_id)
                )
            else:
                cursor.execute(
                    "UPDATE posts SET status = ? WHERE id = ?",
                    (status, post_id)
                )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Update post error: {e}")
            return False