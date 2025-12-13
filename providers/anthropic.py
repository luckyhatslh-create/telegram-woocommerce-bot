import json
from typing import Dict, Any

from anthropic import Anthropic, APIConnectionError, APIStatusError

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)


PROMPT = (
    "You are a product analyst. Extract a strict JSON spec about a knitted hat from the provided photo. "
    "Keep it concise, factual, no marketing tone. Use exact colors, knit pattern, cuff type, patch text/color, pompom presence and color, shape, and materials if visible. "
    "Return only JSON with keys: name (2-4 Russian words), description (2 Russian sentences), color (Russian), category (one of: \"Шапка с помпоном\", \"Шапка слоучи\", \"Шапка бини\", \"Ушанка\", \"Другое\"), "
    "visual (English ultra-detailed hat description for image conditioning)."
)


def extract_product_spec(image_bytes: bytes, client: Anthropic | None = None) -> Dict[str, Any]:
    if not image_bytes:
        raise ValueError("Пустое изображение для анализа")

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
                            "type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_bytes}
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
