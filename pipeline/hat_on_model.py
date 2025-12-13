from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Dict, Any

from PIL import Image

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


def _build_base_prompt(spec: Dict[str, Any]) -> str:
    return (
        "Photorealistic editorial portrait of an adult woman (28-40), neutral background, no hat or headwear, shoulders-up framing. "
        "Calm confident expression, soft daylight. This is a preview run; keep it simple and low-cost."
    )


def _build_fill_prompt(spec: Dict[str, Any]) -> str:
    hat_details = spec.get("visual", "knitted hat, neutral color")
    return (
        "Add the original knitted hat ONLY inside the provided mask. "
        "Preserve exact colors, knit texture, cuff height, patch/label placement, pompom presence and size. "
        f"Hat description: {hat_details}. Do not change face, hair, or background outside the mask. No text overlays."
    )


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

    fill_prompt = _build_fill_prompt(spec)
    final_image_bytes = inpaint_hat(image_to_bytes(base_image, format="PNG"), mask_bytes, fill_prompt, steps)

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

    return PipelineResult(final_image=final_image_bytes, metadata=metadata)
