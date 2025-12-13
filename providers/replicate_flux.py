import requests
from typing import Dict

import replicate

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
    output = client.run(CONFIG.providers.flux_base_model, input=input_payload)
    image_url = output[0] if isinstance(output, list) else str(output)
    return _fetch_image(image_url)


def inpaint_hat(base_image: bytes, mask_image: bytes, prompt: str, steps: int) -> bytes:
    client = replicate.Client(api_token=CONFIG.providers.replicate_api_token)
    input_payload: Dict[str, object] = {
        "prompt": prompt,
        "image": base_image,
        "mask": mask_image,
        "num_inference_steps": steps,
        "disable_safety_checker": True,
    }
    logger.info("Запуск FLUX fill для инпейнтинга")
    output = client.run(CONFIG.providers.flux_fill_model, input=input_payload)
    image_url = output[0] if isinstance(output, list) else str(output)
    return _fetch_image(image_url)
