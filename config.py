import os


class Config:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_TOKEN")
        self.vk_app_id = os.getenv("VK_APP_ID", "")
        self.vk_app_secret = os.getenv("VK_APP_SECRET", "")
        self.vk_redirect_uri = os.getenv("VK_REDIRECT_URI", "https://oauth.vk.com/blank.html")
        self.vk_api_version = os.getenv("VK_API_VERSION", "5.199")


def load_config():
    return Config()