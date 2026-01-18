import logging
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import filters
from datetime import datetime
from config import load_config
from core.database import Database
from core.vk_client import VKClient
from models import User, SocialAccount, Post

logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, config):
        self.config = config
        self.db = Database()
        self.vk_client = VKClient(config)
        self.app = Application.builder().token(config.telegram_token).build()
        self.user_states = {}
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.handle_start))
        self.app.add_handler(CommandHandler("help", self.handle_help))
        self.app.add_handler(CommandHandler("add_vk", self.handle_add_vk))
        self.app.add_handler(CommandHandler("post", self.handle_post))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.db.add_user(User(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        ))
        await update.message.reply_text(
            "Социальный менеджер\n\nКоманды:\n/add_vk - Привязать VK\n/post - Создать пост"
        )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Сначала привяжите VK через /add_vk, затем создайте пост /post")

    async def handle_add_vk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        auth_url = self.vk_client.get_auth_url(user_id)
        await update.message.reply_text(
            f"Перейдите по ссылке для авторизации VK:\n\n{auth_url}\n\nПосле авторизации пришлите код:")
        self.user_states[user_id] = {"awaiting_vk_code": True}

    async def handle_post(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.db.get_user_accounts(user_id):
            await update.message.reply_text("Сначала привяжите VK /add_vk")
            return
        self.user_states[user_id] = {"creating_post": True, "text": "", "platforms": [], "media": []}
        await update.message.reply_text("Пришлите текст поста:")

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text

        if self.user_states.get(user_id, {}).get("awaiting_vk_code"):
            await self.process_vk_auth(user_id, text, update)
            return

        if self.user_states.get(user_id, {}).get("creating_post") and not self.user_states[user_id].get("text"):
            self.user_states[user_id]["text"] = text
            await self.show_platforms(user_id, update)
            return

        await update.message.reply_text("Используйте /start для начала работы")

    async def process_vk_auth(self, user_id: int, code: str, update: Update):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://oauth.vk.com/access_token', params={
                    'client_id': self.config.vk_app_id,
                    'client_secret': self.config.vk_app_secret,
                    'redirect_uri': self.config.vk_redirect_uri,
                    'code': code
                }) as resp:
                    data = await resp.json()

                    if 'error' in data:
                        await update.message.reply_text(
                            f"Ошибка: {data.get('error_description', 'Неизвестная ошибка')}")
                        return

                    access_token = data['access_token']
                    vk_user_id = data['user_id']

                    account = SocialAccount(
                        user_id=user_id,
                        platform="vkontakte",
                        platform_id=str(vk_user_id),
                        username=f"user_{vk_user_id}",
                        access_token=access_token
                    )

                    if self.db.add_social_account(account):
                        await update.message.reply_text("VK аккаунт привязан")
                    else:
                        await update.message.reply_text("Ошибка сохранения")

            if user_id in self.user_states:
                self.user_states[user_id].pop("awaiting_vk_code", None)

        except Exception as e:
            logger.error(f"Ошибка VK: {e}")
            await update.message.reply_text("Ошибка авторизации")

    async def show_platforms(self, user_id: int, update: Update):
        accounts = self.db.get_user_accounts(user_id)
        keyboard = [[InlineKeyboardButton("VK", callback_data="platform_vk")]]
        keyboard.append([InlineKeyboardButton("Опубликовать", callback_data="publish")])

        await update.message.reply_text(
            "Выберите платформы:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if self.user_states.get(user_id, {}).get("creating_post"):
            self.user_states[user_id]["media"].append(update.message.photo[-1].file_id)
            await update.message.reply_text("Фото добавлено")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id

        if query.data == "platform_vk":
            if "vk" in self.user_states[user_id]["platforms"]:
                self.user_states[user_id]["platforms"].remove("vk")
                await query.edit_message_text("VK удален")
            else:
                self.user_states[user_id]["platforms"].append("vk")
                await query.edit_message_text("VK выбран")

        elif query.data == "publish":
            await self.publish_post(user_id, query)

    async def publish_post(self, user_id: int, query):
        state = self.user_states.get(user_id, {})
        if not state or not state.get("platforms"):
            await query.edit_message_text("Выберите платформу")
            return

        post = Post(
            user_id=user_id,
            text=state["text"],
            platforms=state["platforms"],
            media_files=state["media"]
        )

        post_id = self.db.add_post(post)

        results = []
        for platform in state["platforms"]:
            if platform == "vk":
                accounts = self.db.get_user_accounts(user_id, "vkontakte")
                if accounts:
                    account = accounts[0]
                    if self.vk_client.connect(account.access_token):
                        result = self.vk_client.publish_post(f"-{account.platform_id}", state["text"])
                        if result.get('success'):
                            results.append("VK: Опубликовано")
                        else:
                            results.append("VK: Ошибка")
                    else:
                        results.append("VK: Не подключен")
                else:
                    results.append("VK: Нет аккаунта")

        self.db.update_post_status(post_id, "published", datetime.now())

        response = f"Пост #{post_id}\n" + "\n".join(results)
        await query.edit_message_text(response)

        if user_id in self.user_states:
            del self.user_states[user_id]

    async def start(self):
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def stop(self):
        await self.app.updater.stop()
        await self.app.stop()