import asyncio
import json
import os
from datetime import datetime
from io import BytesIO

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ВАЖНО: load_dotenv() должен быть ДО импорта config
load_dotenv()

from config import CONFIG
from pipeline.hat_on_model import generate_hat_on_model
from utils.logging import get_logger

logger = get_logger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Отправьте фото вязаной шапки. Я создам фото взрослой модели и надену именно эту шапку.\n"
        "Режим: preview (экономия токенов, размер до 512px). Для HQ установите переменную STEPS_HQ и MAX_SIZE."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.photo:
        return
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()

    await update.message.reply_text("🤖 Обрабатываю фото: анализ шапки, генерация модели, инпейтинг...")

    try:
        result = await asyncio.get_running_loop().run_in_executor(
            None, lambda: generate_hat_on_model(bytes(photo_bytes))
        )
    except Exception as error:  # noqa: BLE001
        logger.exception("Ошибка пайплайна")
        await update.message.reply_text(
            "❌ Не удалось создать изображение. Проверьте ключи ANTHROPIC/REPLICATE и повторите."
        )
        return

    bio = BytesIO(result.final_image)
    bio.name = "model_hat.png"
    await update.message.reply_photo(photo=bio, caption="✅ Готово! Использован режим preview по умолчанию.")

    metadata = {
        "telegram_file_id": photo_file.file_id,
        "generated_at": datetime.utcnow().isoformat(),
        "pipeline": result.metadata,
    }
    os.makedirs("outputs", exist_ok=True)
    meta_path = os.path.join("outputs", f"metadata_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(meta_path, "w", encoding="utf-8") as fp:
        json.dump(metadata, fp, ensure_ascii=False, indent=2)
    logger.info("Метаданные сохранены: %s", meta_path)

    await update.message.reply_text("💾 Метаданные сохранены. Если нужен HQ режим, задайте QUALITY_MODE=hq или STEPS_HQ.")


def main() -> None:
    """Главная функция запуска бота"""
    token = CONFIG.telegram.token
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logger.info("Бот запущен в режиме %s", CONFIG.pipeline.quality_mode)
    # Используем синхронный метод run_polling для совместимости с Python 3.13
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
