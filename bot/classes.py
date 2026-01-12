from dataclasses import dataclass
from datetime import datetime

@dataclass
class Config:
    telegram_token: str
    vk_app_id: str # айди приложения, нужно для привязки приложения к боту
    vk_app_secret: str # secret token из vk app, тоже нужен для привязки приложения к боту
    vk_service_token: str = "" # токен доступа с ограниченными правами, для возможностей бота


@dataclass
class User:
    telegram_id: int
    username = None
    first_name = None
    last_name = None
    created_at: datetime = None


@dataclass
class SocialAccount:
    user_id: int
    platform: str
    platform_id: str
    access_token: str
    username = None
    created_at: datetime = None


@dataclass
class Post:
    user_id: int
    text: str
    platforms: list
    media_files: list = None
    status: str = "draft"
    scheduled_time = None
    published_at = None
    created_at: datetime = None

@dataclass
class VKClient:
    config = Config
    vk_session = None
    vk = None
    upload = None


class TelegramBot:
    def __init__(self, config):
        self.config = config
        self.vk_client = VKClient(config)
        self.user_states = {}
        self.setup_handlers()