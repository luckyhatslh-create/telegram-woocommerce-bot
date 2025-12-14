from typing import Tuple
from PIL import Image, ImageDraw

from utils.logging import get_logger

logger = get_logger(__name__)


try:  # pragma: no cover - optional dependency
    from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
    _SAM_AVAILABLE = True
except Exception:  # pragma: no cover
    _SAM_AVAILABLE = False


class MaskGenerationError(Exception):
    pass


def _ellipse_mask(size: Tuple[int, int]) -> Image.Image:
    """
    Создает эллиптическую маску для верхней части головы (область шапки).
    ВАЖНО: Маска НЕ должна покрывать глаза, нос или рот!
    """
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)

    # Параметры эллипса для верхней части головы (только макушка)
    # ОБНОВЛЕНО: Маска поднята выше чтобы покрывать ТОЛЬКО макушку
    # Центр эллипса: 0.20 * высоты (самая верхняя часть головы)
    # Высота эллипса: 0.28 * высоты (компактная область)
    # Ширина эллипса: 0.62 * ширины (покрывает ширину головы)
    center_y = height * 0.20
    ellipse_height = height * 0.28
    ellipse_width = width * 0.62

    ellipse_box = (
        width * 0.5 - ellipse_width / 2,   # left
        center_y - ellipse_height / 2,      # top
        width * 0.5 + ellipse_width / 2,   # right
        center_y + ellipse_height / 2,      # bottom
    )

    # Проверяем, что нижняя граница эллипса не опускается ниже 0.39 * height
    # (чтобы НЕ захватить лоб/глаза/лицо - маска ТОЛЬКО на макушке)
    bottom_limit = height * 0.39
    if ellipse_box[3] > bottom_limit:
        logger.warning(
            f"Ellipse bottom {ellipse_box[3]:.0f} exceeds safe limit {bottom_limit:.0f}, adjusting"
        )
        ellipse_box = (ellipse_box[0], ellipse_box[1], ellipse_box[2], bottom_limit)

    draw.ellipse(ellipse_box, fill=255)
    logger.info(f"Fallback ellipse mask: {ellipse_box}, image size: {size}")
    return mask


def create_head_mask(image: Image.Image) -> Image.Image:
    """Generate an alpha mask for the hat area using SAM when available, otherwise ellipse fallback."""
    if image.mode != "RGB":
        image = image.convert("RGB")

    if _SAM_AVAILABLE:
        try:  # pragma: no cover - optional heavy path
            sam = sam_model_registry.get("vit_b")()
            generator = SamAutomaticMaskGenerator(sam)
            masks = generator.generate(image)
            if masks:
                # pick largest mask near top center
                sorted_masks = sorted(masks, key=lambda m: m.get("area", 0), reverse=True)
                chosen = sorted_masks[0]
                mask_image = Image.fromarray(chosen["segmentation"].astype("uint8") * 255)
                return mask_image
        except Exception as error:
            logger.warning("SAM mask generation failed, using ellipse: %s", error)

    logger.info("Using fallback ellipse mask")
    return _ellipse_mask(image.size)


def mask_with_alpha(image: Image.Image, mask_l: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = mask_l.resize(image.size)
    rgba.putalpha(alpha)
    return rgba
