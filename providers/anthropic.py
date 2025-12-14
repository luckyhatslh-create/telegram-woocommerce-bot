import base64
import json
from io import BytesIO
from typing import Dict, Any, Optional

from anthropic import Anthropic, APIConnectionError, APIStatusError
from PIL import Image

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)


PROMPT = (
    "You are a product analyst. Extract a strict JSON spec about a knitted hat from the provided photo. "
    "Keep it concise, factual, no marketing tone. Use exact colors, knit pattern, cuff type, patch text/color, pompom presence and color, shape, and materials if visible. "
    "Return only JSON with keys: name (2-4 Russian words), description (2 Russian sentences), color (Russian), category (one of: \"Шапка с помпоном\", \"Шапка слоучи\", \"Шапка бини\", \"Ушанка\", \"Другое\"), "
    "visual (English ultra-detailed hat description for image conditioning)."
)

HEADWEAR_CHECK_PROMPT = (
    "Look at this portrait photograph carefully. "
    "Is the woman wearing ANY headwear, head covering, or anything on her head? "
    "This includes: hat, cap, beanie, hood, helmet, headband, bandana, scarf, headscarf, hijab, turban, "
    "head wrap, or any fabric/accessory covering any part of the head or hair. "
    "Answer ONLY with YES or NO. "
    "If you see absolutely nothing on the head and the hair is fully visible and uncovered, answer NO. "
    "If there is anything covering the head or hair, answer YES."
)


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SIGNATURE = b"\xff\xd8"


def _normalize_image_payload(image_bytes: bytes) -> tuple[str, bytes]:
    """Определяет тип изображения и при необходимости конвертирует в PNG."""

    if image_bytes.startswith(PNG_SIGNATURE):
        return "image/png", image_bytes

    if image_bytes.startswith(JPEG_SIGNATURE):
        return "image/jpeg", image_bytes

    try:
        image = Image.open(BytesIO(image_bytes))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return "image/png", buffer.getvalue()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Не удалось определить тип изображения, отправляем как PNG: %s", exc)
        return "image/png", image_bytes


def check_headwear_present(image_bytes: bytes, client: Anthropic | None = None) -> Optional[bool]:
    """
    Проверяет наличие головных уборов на изображении через Claude.

    Args:
        image_bytes: Байты изображения для проверки
        client: Опциональный клиент Anthropic

    Returns:
        True если обнаружен головной убор, False если голова чистая, None если проверка не удалась
    """
    if not image_bytes:
        raise ValueError("Пустое изображение для проверки")

    media_type, normalized_bytes = _normalize_image_payload(image_bytes)
    image_b64 = base64.b64encode(normalized_bytes).decode('utf-8')
    client = client or Anthropic(api_key=CONFIG.providers.anthropic_api_key)

    try:
        message = client.messages.create(
            model=CONFIG.providers.anthropic_model,
            max_tokens=10,  # Нужен только YES/NO
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": HEADWEAR_CHECK_PROMPT},
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": media_type, "data": image_b64}
                        },
                    ],
                }
            ],
        )

        if not message.content:
            logger.warning("Пустой ответ Claude при проверке головного убора")
            return None

        response = (message.content[0].text or "").strip().upper()
        if response not in ("YES", "NO"):
            logger.warning("Неверный формат ответа Claude при проверке головного убора: %s", response)
            return None
        logger.info(f"Headwear check response: {response}")

        # Если ответ содержит YES - есть головной убор
        return "YES" in response

    except (APIConnectionError, APIStatusError) as api_error:
        logger.error("Не удалось выполнить проверку головного убора: %s", api_error)
        return None
    except Exception as unexpected_error:  # noqa: BLE001
        logger.error("Неожиданная ошибка проверки головного убора: %s", unexpected_error)
        return None


def extract_product_spec(image_bytes: bytes, client: Anthropic | None = None) -> Dict[str, Any]:
    if not image_bytes:
        raise ValueError("Пустое изображение для анализа")

    media_type, normalized_bytes = _normalize_image_payload(image_bytes)
    image_b64 = base64.b64encode(normalized_bytes).decode('utf-8')

    client = client or Anthropic(api_key=CONFIG.providers.anthropic_api_key)
    try:
        message = client.messages.create(
            model=CONFIG.providers.anthropic_model,
            max_tokens=400,
            temperature=0,
            system="Return only valid minified JSON.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_b64}
                        },
                    ],
                }
            ],
        )
    except (APIConnectionError, APIStatusError) as api_error:
        logger.error("Anthropic API error: %s", api_error)
        raise

    content = message.content[0].text if message.content else "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning("Invalid JSON from model, returning fallback")
        return {
            "name": "Вязаная шапка",
            "description": "Теплая вязаная шапка ручной работы.",
            "color": "неопределенный",
            "category": "Другое",
            "visual": "knitted hat, details unknown",
        }
