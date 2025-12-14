from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from PIL import Image, ImageDraw

from config import CONFIG, QualityMode
from providers.anthropic import extract_product_spec
from providers.replicate_flux import generate_base_model_image, inpaint_hat
from utils.image_hash import sha256_hex
from utils.images import resize_to_max, image_from_bytes, image_to_bytes, ensure_rgb
from utils.logging import get_logger
from utils.mask import create_head_mask

logger = get_logger(__name__)


@dataclass
class PipelineResult:
    final_image: bytes
    metadata: Dict[str, Any]
    overlay_image: Optional[bytes] = None  # Для режима отладки


def _build_base_prompt(spec: Dict[str, Any]) -> str:
    return (
        "Photorealistic editorial portrait of an adult woman (28-40), neutral background, no hat or headwear, shoulders-up framing. "
        "Calm confident expression, soft daylight. This is a preview run; keep it simple and low-cost."
    )


def _build_fill_prompt(spec: Dict[str, Any]) -> str:
    hat_details = spec.get("visual", "knitted hat, neutral color")
    return (
        f"Add a knitted hat ONLY on top of the head inside the provided mask region. "
        f"Hat description: {hat_details}. "
        f"Preserve exact colors, knit texture, cuff height, patch/label placement, pompom presence and size. "
        f"IMPORTANT: This is a HAT, NOT a balaclava, NOT a face mask, NOT a ski mask. "
        f"The hat must ONLY cover the top of the head. "
        f"DO NOT cover eyes, nose, mouth, or face. "
        f"Do not change face, hair, or background outside the mask. No text overlays."
    )


def _create_overlay_image(base_image: Image.Image, mask_l: Image.Image) -> Image.Image:
    """
    Создает изображение overlay для отладки: base + полупрозрачная красная маска.
    """
    overlay = base_image.copy().convert("RGBA")

    # Создаем красную полупрозрачную маску
    red_mask = Image.new("RGBA", base_image.size, (255, 0, 0, 0))
    red_draw = ImageDraw.Draw(red_mask)

    # Конвертируем маску в пиксели
    mask_resized = mask_l.resize(base_image.size)
    for y in range(base_image.size[1]):
        for x in range(base_image.size[0]):
            pixel = mask_resized.getpixel((x, y))
            if pixel > 128:  # Белые области маски
                red_draw.point((x, y), fill=(255, 0, 0, 128))  # Полупрозрачный красный

    # Накладываем красную маску на изображение
    overlay = Image.alpha_composite(overlay, red_mask)
    return overlay.convert("RGB")


def _save_debug_images(request_id: str, base_image: Image.Image, mask_l: Image.Image,
                       final_image_bytes: bytes, overlay: Image.Image) -> None:
    """
    Сохраняет отладочные изображения в папку debug/.
    """
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{timestamp}_{request_id}"

    try:
        base_image.save(debug_dir / f"{prefix}_base.png")
        mask_l.save(debug_dir / f"{prefix}_mask.png")
        overlay.save(debug_dir / f"{prefix}_overlay.png")

        final_image = image_from_bytes(final_image_bytes)
        final_image.save(debug_dir / f"{prefix}_result.png")

        logger.info(f"Debug images saved to {debug_dir} with prefix {prefix}")
    except Exception as e:
        logger.error(f"Failed to save debug images: {e}")


def generate_hat_on_model(product_image: bytes, quality_mode: QualityMode | None = None) -> PipelineResult:
    quality = quality_mode or CONFIG.pipeline.quality_mode
    steps = CONFIG.pipeline.steps_hq if quality == "hq" else CONFIG.pipeline.steps_preview

    resized_bytes, _ = resize_to_max(product_image, CONFIG.pipeline.max_size)
    spec = extract_product_spec(resized_bytes)

    width = height = CONFIG.pipeline.max_size
    base_prompt = _build_base_prompt(spec)
    base_image_bytes = generate_base_model_image(base_prompt, width, height, steps)
    base_image = ensure_rgb(image_from_bytes(base_image_bytes))

    mask_l = create_head_mask(base_image)
    mask_bytes = image_to_bytes(mask_l, format="PNG")

    # Создаем overlay изображение для отладки (если включен режим MASK_DEBUG)
    overlay_bytes = None
    if CONFIG.pipeline.mask_debug:
        overlay = _create_overlay_image(base_image, mask_l)
        overlay_bytes = image_to_bytes(overlay, format="PNG")

    fill_prompt = _build_fill_prompt(spec)
    final_image_bytes = inpaint_hat(image_to_bytes(base_image, format="PNG"), mask_bytes, fill_prompt, steps)

    # Сохраняем отладочные изображения если включен режим MASK_DEBUG
    if CONFIG.pipeline.mask_debug:
        request_id = sha256_hex(product_image)[:8]
        overlay_for_save = _create_overlay_image(base_image, mask_l)
        _save_debug_images(request_id, base_image, mask_l, final_image_bytes, overlay_for_save)

    metadata = {
        "spec": spec,
        "quality_mode": quality,
        "steps": steps,
        "hashes": {
            "product": sha256_hex(product_image),
            "base": sha256_hex(base_image_bytes),
            "final": sha256_hex(final_image_bytes),
        },
        "preview_note": "Используется режим preview (низкая стоимость)" if quality != "hq" else "HQ",
    }

    return PipelineResult(final_image=final_image_bytes, metadata=metadata, overlay_image=overlay_bytes)
