import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    openai_model: str = "gpt-4.1-mini"
    max_output_tokens: int = 700

    @classmethod
    def from_env(cls) -> "Settings":
        missing_vars = [
            name
            for name in ("TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY")
            if not os.getenv(name)
        ]
        if missing_vars:
            raise RuntimeError(
                "Missing environment variables: " + ", ".join(missing_vars)
            )

        return cls(
            telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "700")),
        )


settings = Settings.from_env()
client = AsyncOpenAI()

previous_responses: dict[int, str] = {}
user_locks: dict[int, asyncio.Lock] = {}

SYSTEM_PROMPT = (
    "You are a friendly Ukrainian AI assistant inside a Telegram bot. "
    "Answer clearly, briefly, and helpfully. If the user asks about code, "
    "explain step by step for a beginner."
)


def get_user_lock(user_id: int) -> asyncio.Lock:
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]


def split_telegram_message(text: str) -> list[str]:
    return [
        text[index : index + TELEGRAM_MESSAGE_LIMIT]
        for index in range(0, len(text), TELEGRAM_MESSAGE_LIMIT)
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        "Привіт! Я AI-асистент у Telegram.\n\n"
        "Напиши питання, а я відповім. Команди:\n"
        "/help - що я вмію\n"
        "/reset - очистити контекст розмови"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    await update.message.reply_text(
        "Я можу відповідати на питання, пояснювати код, допомагати з навчанням "
        "і пам'ятати контекст поточної розмови.\n\n"
        "Якщо хочеш почати з чистого аркуша, напиши /reset."
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    previous_responses.pop(update.effective_user.id, None)
    await update.message.reply_text("Контекст очищено. Можемо почати заново.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_message = update.message.text.strip()

    if not user_message:
        return

    lock = get_user_lock(user_id)
    if lock.locked():
        await update.message.reply_text("Я ще обробляю попереднє повідомлення. Секунду.")
        return

    async with lock:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )

        try:
            response_kwargs = {
                "model": settings.openai_model,
                "instructions": SYSTEM_PROMPT,
                "input": user_message,
                "max_output_tokens": settings.max_output_tokens,
            }

            if user_id in previous_responses:
                response_kwargs["previous_response_id"] = previous_responses[user_id]

            response = await client.responses.create(**response_kwargs)

            previous_responses[user_id] = response.id
            answer = response.output_text.strip()

            if not answer:
                answer = "Вибач, я не зміг згенерувати відповідь. Спробуй ще раз."

            for message_part in split_telegram_message(answer):
                await update.message.reply_text(message_part)

        except Exception:
            logger.exception("Failed to process message from user %s", user_id)
            await update.message.reply_text(
                "Вибач, сталася помилка під час обробки запиту. Спробуй пізніше."
            )


def main() -> None:
    logger.info("Starting Telegram AI bot with model %s", settings.openai_model)

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
