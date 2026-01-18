from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class SocialAccount:
    user_id: int
    platform: str
    platform_id: str
    access_token: str
    username: Optional[str] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class Post:
    user_id: int
    text: str
    platforms: List[str]
    media_files: List[str] = None
    status: str = "draft"
    published_at: Optional[datetime] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.media_files is None:
            self.media_files = []