import asyncio
import logging
from dotenv import load_dotenv
from config import load_config
from bot.telegram_bot import TelegramBot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    load_dotenv()
    config = load_config()

    if not config.telegram_token:
        logger.error("Нет TELEGRAM_TOKEN")
        return

    bot = TelegramBot(config)

    try:
        await bot.start()
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Остановка")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())