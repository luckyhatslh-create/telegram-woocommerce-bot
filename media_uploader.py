"""
Модуль для загрузки изображений в WordPress Media Library
"""
import os
import base64
import requests
from typing import Optional, List
from io import BytesIO
from PIL import Image


def compress_image(img_data: bytes, max_size: int = 800, quality: int = 70) -> bytes:
    """Сжатие изображения"""
    try:
        img = Image.open(BytesIO(img_data))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Ошибка сжатия изображения: {e}")
        return img_data


def upload_image_to_media(
    image_data: bytes,
    filename: str,
    wp_url: str,
    wp_username: str,
    wp_app_password: str
) -> Optional[dict]:
    """
    Загрузка изображения в WordPress Media Library

    Args:
        image_data: Байты изображения
        filename: Имя файла
        wp_url: URL WordPress сайта
        wp_username: Имя пользователя WordPress
        wp_app_password: Application Password

    Returns:
        Словарь с данными загруженного изображения или None при ошибке
    """
    if not wp_url.endswith('/'):
        wp_url += '/'

    media_url = f"{wp_url}wp-json/wp/v2/media"

    headers = {
        'Content-Type': 'image/jpeg',
        'Content-Disposition': f'attachment; filename="{filename}"'
    }

    try:
        # Сжимаем изображение перед загрузкой
        compressed_data = compress_image(image_data, max_size=1200, quality=80)

        response = requests.post(
            media_url,
            data=compressed_data,
            headers=headers,
            auth=(wp_username, wp_app_password),
            timeout=60
        )

        if response.status_code == 201:
            media_data = response.json()
            return {
                'id': media_data['id'],
                'url': media_data['source_url'],
                'title': media_data['title']['rendered']
            }
        else:
            print(f"Ошибка загрузки в Media Library: {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return None

    except Exception as e:
        print(f"Исключение при загрузке изображения: {e}")
        return None


def upload_image_from_url(
    image_url: str,
    filename: str,
    wp_url: str,
    wp_username: str,
    wp_app_password: str
) -> Optional[dict]:
    """
    Загрузка изображения из URL в WordPress Media Library

    Args:
        image_url: URL изображения
        filename: Имя файла
        wp_url: URL WordPress сайта
        wp_username: Имя пользователя WordPress
        wp_app_password: Application Password

    Returns:
        Словарь с данными загруженного изображения или None при ошибке
    """
    try:
        # Скачиваем изображение
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()

        # Загружаем в Media Library
        return upload_image_to_media(
            response.content,
            filename,
            wp_url,
            wp_username,
            wp_app_password
        )

    except Exception as e:
        print(f"Ошибка при скачивании/загрузке изображения из {image_url}: {e}")
        return None


def upload_images_batch(
    image_urls: List[str],
    wp_url: str,
    wp_username: str,
    wp_app_password: str
) -> List[dict]:
    """
    Массовая загрузка изображений

    Args:
        image_urls: Список URL изображений
        wp_url: URL WordPress сайта
        wp_username: Имя пользователя WordPress
        wp_app_password: Application Password

    Returns:
        Список словарей с данными загруженных изображений
    """
    uploaded_images = []

    for idx, img_url in enumerate(image_urls):
        print(f"Загрузка изображения {idx + 1}/{len(image_urls)}...")

        filename = f"product_image_{idx}_{os.urandom(4).hex()}.jpg"
        result = upload_image_from_url(img_url, filename, wp_url, wp_username, wp_app_password)

        if result:
            uploaded_images.append({'id': result['id']})
            print(f"✅ Изображение {idx + 1} загружено (ID: {result['id']})")
        else:
            print(f"❌ Не удалось загрузить изображение {idx + 1}")

    return uploaded_images
