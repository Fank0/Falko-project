import vk_api
from vk_api.upload import VkUpload
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class VKClient:
    def __init__(self, config):
        self.config = config
        self.vk = None

    def connect(self, access_token: str) -> bool:
        try:
            vk_session = vk_api.VkApi(token=access_token, api_version=self.config.vk_api_version)
            self.vk = vk_session.get_api()
            self.vk.users.get()
            return True
        except Exception as e:
            logger.error(f"VK connect error: {e}")
            return False

    def publish_post(self, owner_id: str, text: str) -> dict:
        if not self.vk:
            return {'success': False, 'error': 'Not connected'}

        try:
            result = self.vk.wall.post(owner_id=owner_id, message=text, from_group=1)
            return {'success': True, 'post_id': result['post_id']}
        except Exception as e:
            logger.error(f"VK post error: {e}")
            return {'success': False, 'error': str(e)}

    def get_auth_url(self, user_id: int) -> str:
        params = {
            'client_id': self.config.vk_app_id,
            'redirect_uri': self.config.vk_redirect_uri,
            'scope': 'wall,photos,groups,offline',
            'response_type': 'code',
            'display': 'page',
            'v': self.config.vk_api_version
        }
        if user_id:
            params['state'] = str(user_id)

        return f"https://oauth.vk.com/authorize?{urlencode(params)}"