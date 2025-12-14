import base64
import json
from typing import Dict, Any

from anthropic import Anthropic, APIConnectionError, APIStatusError

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)


def _raise_if_model_missing(api_error: APIStatusError) -> None:
    model_name = CONFIG.providers.anthropic_model
    status_code = getattr(api_error, "status_code", None)

    if status_code == 404:
        raise RuntimeError(f"Anthropic model not found or no access: {model_name}") from api_error

    error_candidates = []

    if hasattr(api_error, "response") and hasattr(api_error.response, "json"):
        try:
            error_candidates.append(api_error.response.json())
        except Exception:  # noqa: BLE001
            pass

    if hasattr(api_error, "body"):
        error_candidates.append(getattr(api_error, "body"))

    if hasattr(api_error, "error"):
        error_candidates.append(getattr(api_error, "error"))

    for candidate in error_candidates:
        if isinstance(candidate, dict):
            nested = candidate.get("error") if isinstance(candidate.get("error"), dict) else None
            nested_candidates = [candidate]
            if nested:
                nested_candidates.append(nested)

            for nested_candidate in nested_candidates:
                if isinstance(nested_candidate, dict) and nested_candidate.get("type") == "not_found_error":
                    raise RuntimeError(
                        f"Anthropic model not found or no access: {model_name}"
                    ) from api_error
        elif getattr(candidate, "type", None) == "not_found_error":
            raise RuntimeError(f"Anthropic model not found or no access: {model_name}") from api_error

    if "not_found_error" in str(api_error):
        raise RuntimeError(f"Anthropic model not found or no access: {model_name}") from api_error


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


def check_headwear_present(image_bytes: bytes, client: Anthropic | None = None) -> bool:
    """
    Проверяет наличие головных уборов на изображении через Claude.

    Args:
        image_bytes: Байты изображения для проверки
        client: Опциональный клиент Anthropic

    Returns:
        True если обнаружен головной убор, False если голова чистая
    """
    if not image_bytes:
        raise ValueError("Пустое изображение для проверки")

    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
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
                            "source": {"type": "base64", "media_type": "image/png", "data": image_b64}
                        },
                    ],
                }
            ],
        )

        response = message.content[0].text.strip().upper() if message.content else "YES"
        logger.info(f"Headwear check response: {response}")

        # Если ответ содержит YES - есть головной убор
        return "YES" in response

    except (APIConnectionError, APIStatusError) as api_error:
        if isinstance(api_error, APIStatusError):
            _raise_if_model_missing(api_error)

        logger.error("Anthropic API error during headwear check: %s", api_error)
        # В случае ошибки API - считаем что headwear есть (безопаснее)
        return True


def extract_product_spec(image_bytes: bytes, client: Anthropic | None = None) -> Dict[str, Any]:
    if not image_bytes:
        raise ValueError("Пустое изображение для анализа")

    # Конвертируем байты в base64 строку
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

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
                            "type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}
                        },
                    ],
                }
            ],
        )
    except (APIConnectionError, APIStatusError) as api_error:
        if isinstance(api_error, APIStatusError):
            _raise_if_model_missing(api_error)

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
