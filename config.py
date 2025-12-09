"""
Конфигурация бота
"""
import os
from typing import Dict, List

# Настройки категорий товаров
PRODUCT_CATEGORIES = {
    "Шапка с помпоном": {
        "prompt": "wearing a knitted hat with a pompom on her head",
        "aliases": ["шапка с бубоном", "помпон", "с помпоном"]
    },
    "Шапка слоучи": {
        "prompt": "wearing a slouchy knitted beanie hat",
        "aliases": ["слоучи", "slouchy", "свободная шапка"]
    },
    "Шапка бини": {
        "prompt": "wearing a fitted beanie hat",
        "aliases": ["бини", "beanie", "обтягивающая шапка"]
    },
    "Ушанка": {
        "prompt": "wearing a ushanka winter hat with ear flaps",
        "aliases": ["ушанка", "шапка ушанка", "с ушами"]
    },
    "Шарф": {
        "prompt": "wearing a knitted scarf around her neck",
        "aliases": ["шарф", "шарфик", "снуд"]
    },
    "Платье": {
        "prompt": "wearing a knitted dress",
        "aliases": ["платье", "вязаное платье"]
    },
    "Топ": {
        "prompt": "wearing a knitted top",
        "aliases": ["топ", "кофта", "блуза"]
    },
    "Варежки": {
        "prompt": "wearing knitted mittens on her hands",
        "aliases": ["варежки", "рукавицы", "перчатки"]
    },
    "Носки": {
        "prompt": "wearing knitted socks",
        "aliases": ["носки", "гольфы"]
    },
    "Свитер": {
        "prompt": "wearing a knitted sweater",
        "aliases": ["свитер", "джемпер", "пуловер"]
    }
}

# Настройки OpenAI
OPENAI_CONFIG = {
    # Модель для анализа изображений
    "vision_model": "gpt-4o",
    
    # Модель для генерации изображений
    "image_model": "dall-e-3",
    
    # Параметры генерации изображений
    "image_size": "1024x1024",  # Варианты: "1024x1024", "1792x1024", "1024x1792"
    "image_quality": "standard",  # Варианты: "standard", "hd"
    
    # Параметры анализа
    "vision_max_tokens": 500,
    "vision_temperature": 0.7,
    
    # Количество фото для анализа (для экономии токенов)
    "photos_to_analyze": 2
}

# Промпт для анализа товара
ANALYSIS_PROMPT = """Проанализируй эти фотографии товара (вероятно вязаное изделие).

Определи:
1. Название товара (краткое, привлекательное, на русском языке)
2. Подробное описание (2-3 предложения на русском, включая детали вязки, стиль, особенности)
3. Основной цвет (на русском)
4. Категорию товара из списка: "Шапка с помпоном", "Шапка слоучи", "Шапка бини", "Ушанка", "Шарф", "Платье", "Топ", "Варежки", "Носки", "Свитер", "Другое"

Верни ответ СТРОГО в формате JSON:
{
  "name": "название",
  "description": "описание",
  "color": "цвет",
  "category": "категория"
}"""

# Промпт для генерации изображения модели
MODEL_PHOTO_PROMPT_TEMPLATE = """Professional product photography: Beautiful young woman with natural makeup on pure white background, {item_description}. 
The {category} is {color} color, made of {material}.
Studio lighting, high fashion style, photorealistic, 8k quality, clean white backdrop, centered composition, professional model pose.
Focus on showing the product clearly."""

# Настройки WooCommerce
WOOCOMMERCE_CONFIG = {
    # Статус товара по умолчанию
    "default_status": "draft",  # "draft" или "publish"
    
    # Таксономии
    "manage_stock": False,
    "stock_quantity": None,
    
    # Добавлять ли водяной знак
    "add_watermark": False
}

# Настройки Telegram
TELEGRAM_CONFIG = {
    # Максимальное количество фотографий
    "max_photos": 4,
    
    # Минимальное количество фотографий
    "min_photos": 1,
    
    # Таймаут для операций
    "operation_timeout": 120,
    
    # Сообщения
    "messages": {
        "start": "👋 Привет! Я помогу добавить товар в WooCommerce.\n\n📸 Пожалуйста, отправьте 3-4 фотографии товара.\nКогда закончите, отправьте команду /done",
        "photo_received": "✅ Фото {current}/{max} получено.\nОтправьте еще фото или /done для продолжения.",
        "max_photos_reached": "⚠️ Максимум {max} фотографии. Отправьте /done для продолжения.",
        "analyzing": "🤖 Анализирую фотографии с помощью AI...\nЭто может занять несколько секунд.",
        "generating_photo": "🎨 Генерирую фотореалистичное изображение модели с товаром...\nЭто займет около 30 секунд.",
        "upload_success": "✅ Товар успешно добавлен в магазин!\n\n🔗 ID товара: {id}\n📦 Название: {name}\n💰 Цена: {price} руб.\n\nДля добавления нового товара используйте /start",
        "upload_error": "❌ Ошибка при загрузке: {error}\n\nПопробуйте снова или начните заново /start"
    }
}

# Лимиты и ограничения
LIMITS = {
    # Максимальный размер фото в МБ
    "max_photo_size_mb": 20,
    
    # Минимальное разрешение фото
    "min_photo_resolution": (400, 400),
    
    # Максимальная длина названия
    "max_name_length": 100,
    
    # Максимальная длина описания
    "max_description_length": 2000,
    
    # Минимальная цена
    "min_price": 0,
    
    # Максимальная цена
    "max_price": 1000000
}

# Логирование
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "bot.log"
}


def get_category_prompt(category: str, color: str, material: str) -> str:
    """
    Получить промпт для генерации изображения по категории
    
    Args:
        category: Категория товара
        color: Цвет товара
        material: Материал товара
    
    Returns:
        Промпт для DALL-E
    """
    category_info = PRODUCT_CATEGORIES.get(category)
    
    if category_info:
        item_description = category_info["prompt"]
    else:
        item_description = f"wearing a {category.lower()}"
    
    return MODEL_PHOTO_PROMPT_TEMPLATE.format(
        item_description=item_description,
        category=category.lower(),
        color=color,
        material=material
    )


def validate_price(price: str) -> tuple[bool, float | str]:
    """
    Валидация цены
    
    Args:
        price: Строка с ценой
    
    Returns:
        (is_valid, price_value_or_error_message)
    """
    try:
        price_value = float(price.replace(',', '.'))
        
        if price_value < LIMITS["min_price"]:
            return False, f"Цена должна быть больше {LIMITS['min_price']}"
        
        if price_value > LIMITS["max_price"]:
            return False, f"Цена должна быть меньше {LIMITS['max_price']}"
        
        return True, price_value
    except ValueError:
        return False, "Неверный формат цены. Введите число (например: 1500 или 1500.50)"


def validate_text_length(text: str, field_name: str) -> tuple[bool, str]:
    """
    Валидация длины текста
    
    Args:
        text: Текст для проверки
        field_name: Название поля (для сообщения об ошибке)
    
    Returns:
        (is_valid, error_message)
    """
    if field_name == "name":
        max_length = LIMITS["max_name_length"]
    elif field_name == "description":
        max_length = LIMITS["max_description_length"]
    else:
        return True, ""
    
    if len(text) > max_length:
        return False, f"{field_name} слишком длинное. Максимум {max_length} символов."
    
    return True, ""
