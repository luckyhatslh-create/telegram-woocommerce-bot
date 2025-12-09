"""
Утилиты для обработки изображений
"""
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional


def resize_image(image_data: bytes, max_size: Tuple[int, int] = (2048, 2048)) -> bytes:
    """
    Изменяет размер изображения, сохраняя пропорции
    
    Args:
        image_data: Байты изображения
        max_size: Максимальный размер (ширина, высота)
    
    Returns:
        Байты измененного изображения
    """
    img = Image.open(BytesIO(image_data))
    
    # Конвертируем в RGB если нужно
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Изменяем размер
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Сохраняем в байты
    output = BytesIO()
    img.save(output, format='JPEG', quality=85, optimize=True)
    return output.getvalue()


def optimize_image_for_telegram(image_data: bytes) -> bytes:
    """
    Оптимизирует изображение для отправки в Telegram
    Telegram рекомендует размер не более 10MB и разрешение 2560x2560
    
    Args:
        image_data: Байты изображения
    
    Returns:
        Оптимизированные байты изображения
    """
    img = Image.open(BytesIO(image_data))
    
    # Конвертируем в RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Уменьшаем до разумного размера
    max_dimension = 2560
    if img.width > max_dimension or img.height > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    # Сохраняем с оптимизацией
    output = BytesIO()
    img.save(output, format='JPEG', quality=90, optimize=True)
    
    return output.getvalue()


def compress_image(image_data: bytes, target_size_kb: int = 500) -> bytes:
    """
    Сжимает изображение до целевого размера
    
    Args:
        image_data: Байты изображения
        target_size_kb: Целевой размер в килобайтах
    
    Returns:
        Сжатые байты изображения
    """
    img = Image.open(BytesIO(image_data))
    
    # Конвертируем в RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Начинаем с высокого качества
    quality = 95
    
    while quality > 20:
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        size_kb = len(output.getvalue()) / 1024
        
        if size_kb <= target_size_kb:
            return output.getvalue()
        
        quality -= 5
    
    # Если не удалось сжать до нужного размера, уменьшаем разрешение
    scale = 0.9
    while scale > 0.3:
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        output = BytesIO()
        resized.save(output, format='JPEG', quality=85, optimize=True)
        size_kb = len(output.getvalue()) / 1024
        
        if size_kb <= target_size_kb:
            return output.getvalue()
        
        scale -= 0.1
    
    # Возвращаем максимально сжатое изображение
    return output.getvalue()


def get_image_info(image_data: bytes) -> dict:
    """
    Получает информацию об изображении
    
    Args:
        image_data: Байты изображения
    
    Returns:
        Словарь с информацией об изображении
    """
    img = Image.open(BytesIO(image_data))
    
    return {
        'width': img.width,
        'height': img.height,
        'format': img.format,
        'mode': img.mode,
        'size_bytes': len(image_data),
        'size_kb': len(image_data) / 1024,
        'size_mb': len(image_data) / (1024 * 1024)
    }


def create_thumbnail(image_data: bytes, size: Tuple[int, int] = (300, 300)) -> bytes:
    """
    Создает миниатюру изображения
    
    Args:
        image_data: Байты изображения
        size: Размер миниатюры
    
    Returns:
        Байты миниатюры
    """
    img = Image.open(BytesIO(image_data))
    
    # Конвертируем в RGB
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Создаем миниатюру
    img.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Сохраняем
    output = BytesIO()
    img.save(output, format='JPEG', quality=85)
    
    return output.getvalue()
