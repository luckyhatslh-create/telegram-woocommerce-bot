import base64
import time
import requests
from typing import Dict

import httpx
import replicate
from replicate.exceptions import ReplicateError

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)


def _fetch_image(url: str) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def generate_base_model_image(prompt: str, width: int, height: int, steps: int) -> bytes:
    client = replicate.Client(api_token=CONFIG.providers.replicate_api_token)
    input_payload: Dict[str, object] = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_inference_steps": steps,
        "disable_safety_checker": True,
    }
    logger.info("Запуск FLUX base генерации: %s", input_payload)

    # Retry logic для обработки rate limiting (429 errors) и timeouts
    max_retries = 5  # Увеличено до 5 попыток из-за rate limiting
    for attempt in range(max_retries):
        try:
            output = client.run(CONFIG.providers.flux_base_model, input=input_payload)
            break
        except ReplicateError as e:
            if e.status == 429 and attempt < max_retries - 1:
                # При rate limit ждем дольше с каждой попыткой (exponential backoff)
                wait_time = 15 * (attempt + 1)  # 15s, 30s, 45s, 60s
                logger.warning(f"Rate limit достигнут, ожидание {wait_time}s перед попыткой {attempt + 2}/{max_retries}")
                time.sleep(wait_time)
            else:
                logger.error(f"Replicate API error после {attempt + 1} попыток: %s", e)
                raise
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as timeout_error:
            if attempt < max_retries - 1:
                wait_time = 10
                logger.warning(f"Timeout error, повторная попытка {attempt + 2}/{max_retries} через {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error(f"Timeout после {attempt + 1} попыток: %s", timeout_error)
                raise

    image_url = output[0] if isinstance(output, list) else str(output)
    return _fetch_image(image_url)


def inpaint_hat(base_image: bytes, mask_image: bytes, prompt: str, steps: int) -> bytes:
    client = replicate.Client(api_token=CONFIG.providers.replicate_api_token)

    # Конвертируем изображения в data URIs для Replicate API
    base_image_uri = f"data:image/png;base64,{base64.b64encode(base_image).decode('utf-8')}"
    mask_image_uri = f"data:image/png;base64,{base64.b64encode(mask_image).decode('utf-8')}"

    input_payload: Dict[str, object] = {
        "prompt": prompt,
        "image": base_image_uri,
        "mask": mask_image_uri,
        "num_inference_steps": steps,
        "disable_safety_checker": True,
    }
    logger.info("Запуск FLUX fill для инпейнтинга")

    # Retry logic для обработки rate limiting (429 errors) и timeouts
    max_retries = 5  # Увеличено до 5 попыток из-за rate limiting
    for attempt in range(max_retries):
        try:
            output = client.run(CONFIG.providers.flux_fill_model, input=input_payload)
            break
        except ReplicateError as e:
            if e.status == 429 and attempt < max_retries - 1:
                # При rate limit ждем дольше с каждой попыткой (exponential backoff)
                wait_time = 15 * (attempt + 1)  # 15s, 30s, 45s, 60s
                logger.warning(f"Rate limit достигнут, ожидание {wait_time}s перед попыткой {attempt + 2}/{max_retries}")
                time.sleep(wait_time)
            else:
                logger.error(f"Replicate API error после {attempt + 1} попыток: %s", e)
                raise
        except (httpx.ReadTimeout, httpx.ConnectTimeout) as timeout_error:
            if attempt < max_retries - 1:
                wait_time = 10
                logger.warning(f"Timeout error, повторная попытка {attempt + 2}/{max_retries} через {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error(f"Timeout после {attempt + 1} попыток: %s", timeout_error)
                raise

    image_url = output[0] if isinstance(output, list) else str(output)
    return _fetch_image(image_url)
