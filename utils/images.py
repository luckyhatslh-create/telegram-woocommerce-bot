from io import BytesIO
from typing import Tuple
from PIL import Image


def resize_to_max(image_bytes: bytes, max_size: int) -> tuple[bytes, Tuple[int, int]]:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image.thumbnail((max_size, max_size))
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue(), image.size


def image_from_bytes(image_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(image_bytes))


def image_to_bytes(image: Image.Image, format: str = "PNG") -> bytes:
    buf = BytesIO()
    image.save(buf, format=format)
    return buf.getvalue()


def ensure_rgb(image: Image.Image) -> Image.Image:
    if image.mode != "RGB":
        return image.convert("RGB")
    return image
