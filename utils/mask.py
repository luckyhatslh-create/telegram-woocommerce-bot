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
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    ellipse_box = (
        width * 0.2,
        height * 0.05,
        width * 0.8,
        height * 0.55,
    )
    draw.ellipse(ellipse_box, fill=255)
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
