import os
import asyncio
import base64
import json
from io import BytesIO
from typing import List, Dict, Optional
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv
load_dotenv()
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from openai import OpenAI
from woocommerce import API

# Состояния разговора
WAITING_PHOTOS, WAITING_MATERIAL, WAITING_SIZE, WAITING_PRICE, WAITING_CONFIRMATION = range(5)

# Инициализация клиентов
openai_client = OpenAI()

wcapi = API(
    url=os.getenv('WC_URL'),
    consumer_key=os.getenv('WC_KEY'),
    consumer_secret=os.getenv('WC_SECRET'),
    version="wc/v3",
    timeout=120  # Увеличенный timeout для загрузки изображений
)


class ProductData:
    """Класс для хранения данных о продукте"""
    def __init__(self):
        self.photos: List[bytes] = []
        self.photo_ids: List[str] = []
        self.name: str = ""
        self.description: str = ""
        self.color: str = ""
        self.category: str = ""
        self.material: str = ""
        self.size: str = ""
        self.price: str = ""
        self.generated_image: Optional[bytes] = None
        self.use_generated_image: bool = True
        self.visual_description: str = ""  # Детальное визуальное описание для генерации фото
        self.photo_urls: List[str] = []  # URL исходных фото
        self.generated_image_url: str = ""  # URL сгенерированного фото


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало работы сботом"""
    context.user_data['product'] = ProductData()
    
    await update.message.reply_text(
        "👋 Привет! Я помогу добавить товар в WooCommerce.\n\n"
        "📸 Пожалуйста, отправьте 3-4 фотографии товара.\n"
        "Когда закончите, отправьте команду /done"
    )
    return WAITING_PHOTOS

def compress_image(img_data: bytes, max_size: int = 800, quality: int = 70) -> bytes:
    """Сжатие изображения для ускорения загрузки"""
    try:
        img = Image.open(BytesIO(img_data))
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        # Изменяем размер
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        # Сохраняем с компрессией
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Ошибка сжатия: {e}")
        return img_data


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение фотографий от пользователя"""
    product: ProductData = context.user_data.get('product')
    
    if len(product.photos) >= 4:
        await update.message.reply_text(
            "⚠️ Максимум 4 фотографии. Отправьте /done для продолжения."
        )
        return WAITING_PHOTOS
    
    # Получаем файл фото
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Сохраняем URL файла (доступен 1 час)
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    file_url = f"https://api.telegram.org/file/bot{bot_token}/{photo_file.file_path}"
    
    product.photos.append(bytes(photo_bytes))
    product.photo_urls.append(file_url)
    product.photo_ids.append(update.message.photo[-1].file_id)
    
    await update.message.reply_text(
        f"✅ Фото {len(product.photos)}/4 получено.\n"
        f"Отправьте еще фото или /done для продолжения."
    )
    
    return WAITING_PHOTOS


async def photos_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка завершения загрузки фото"""
    product: ProductData = context.user_data.get('product')
    
    if len(product.photos) < 1:
        await update.message.reply_text(
            "⚠️ Нужно отправить хотя бы одно фото!"
        )
        return WAITING_PHOTOS
    
    await update.message.reply_text(
        "🤖 Анализирую фотографии с помощью AI...\n"
        "Это может занять несколько секунд."
    )
    
    # Анализ фотографий с помощью GPT-4 Vision
    try:
        analysis = await analyze_photos(product.photos)
        
        product.name = analysis.get('name', 'Товар')
        product.description = analysis.get('description', '')
        product.color = analysis.get('color', '')
        product.category = analysis.get('category', 'Без категории')
        product.visual_description = analysis.get('visual_description', '')
        
        await update.message.reply_text(
            f"✨ Анализ завершен!\n\n"
            f"📦 Название: {product.name}\n"
            f"🎨 Цвет: {product.color}\n"
            f"📁 Категория: {product.category}\n\n"
            f"📝 Описание:\n{product.description}\n\n"
            f"🧵 Укажите материал изделия:"
        )
        
        return WAITING_MATERIAL
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при анализе: {str(e)}\n"
            f"Попробуйте снова /start"
        )
        return ConversationHandler.END


async def analyze_photos(photos: List[bytes]) -> Dict:
    """Анализ фотографий с помощью OpenAI Vision"""
    # Конвертируем фото в base64
    base64_images = []
    for photo in photos[:2]:  # Используем первые 2 фото для экономии токенов
        base64_image = base64.b64encode(photo).decode('utf-8')
        base64_images.append(base64_image)
    
    # Создаем промпт для детального анализа
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": """Внимательно и МАКСИМАЛЬНО детально проанализируй эти фотографии товара (вязаное изделие ручной работы).

Проведи ОЧЕНЬ тщательный анализ и определи:

1. **Название товара** — придумай привлекательное, продающее название для интернет-магазина (2-4 слова)

2. **Подробное описание** — составь детальное описание товара (4-6 предложений), включая:
   - Тип вязки (косы, араны, резинка, гладь, ажур и т.д.)
   - Стиль изделия (классический, современный, молодежный, романтичный)
   - Особенности кроя и посадки
   - Декоративные элементы (помпон, отворот, кисточки и т.д.)
   - Для каких случаев подходит (повседневная носка, прогулки, спорт)
   - Сезонность и практичность

3. **Основной цвет** — укажи точное название цвета (не просто "красный", а "бордовый", "алый", "терракотовый" и т.д.)

4. **Категорию товара** из списка: "Шапка с помпоном", "Шапка слоучи", "Шапка бини", "Ушанка", "Шарф", "Платье", "Топ", "Другое"

5. **ДЕТАЛЬНОЕ ВИЗУАЛЬНОЕ ОПИСАНИЕ для генерации ИДЕНТИЧНОГО фото** (КРИТИЧЕСКИ ВАЖНО!) — опиши на АНГЛИЙСКОМ языке ТОЧНЫЙ внешний вид для создания максимально похожего изображения:

   ЦВЕТА (COLORS) - ОЧЕНЬ ТОЧНО:
   - Точные названия цветов (например: "dark burgundy/maroon", "pure white/cream", "bright turquoise/teal blue")
   - Процентное соотношение цветов если возможно
   
   УЗОР/ПОЛОСЫ (PATTERN):
   - Точный порядок полос СВЕРХУ ВНИЗ (например: "Starting from TOP: burgundy band, then white stripe, then turquoise stripe, then burgundy main body")
   - Ширина каждой полосы относительно других
   
   ПОМПОН (POMPOM):
   - Точный цвет помпона
   - Размер (большой/средний/маленький)
   - Текстура (пушистый/плотный)
   
   ВЯЗКА (KNIT TEXTURE):
   - Тип вязки (chunky ribbed knit, cable knit, stockinette)
   - Плотность вязки
   
   ФОРМА (SHAPE):
   - Форма изделия (slouchy, fitted, beanie style, with fold-up brim)

Верни ответ СТРОГО в формате JSON:
{
  "name": "название",
  "description": "подробное описание на русском",
  "color": "точный цвет",
  "category": "категория",
  "visual_description": "VERY DETAILED English description: colors, pattern order from top to bottom, pompom color and size, knit texture, shape - be extremely specific"
}"""
                }
            ] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img}",
                        "detail": "high"
                    }
                } for img in base64_images
            ]
        }
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        temperature=0.5
    )
    
    # Парсим JSON из ответа
    content = response.choices[0].message.content
    
    # Убираем возможные markdown блоки
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    return json.loads(content.strip())


async def receive_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение материала изделия"""
    product: ProductData = context.user_data.get('product')
    product.material = update.message.text.strip()
    
    await update.message.reply_text(
        f"✅ Материал: {product.material}\n\n"
        f"📏 Укажите размер изделия:"
    )
    
    return WAITING_SIZE


async def receive_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение размера изделия"""
    product: ProductData = context.user_data.get('product')
    product.size = update.message.text.strip()
    
    await update.message.reply_text(
        f"✅ Размер: {product.size}\n\n"
        f"💰 Укажите стоимость в рублях (только число):"
    )
    
    return WAITING_PRICE


async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение цены и генерация фото модели"""
    product: ProductData = context.user_data.get('product')
    
    try:
        price = float(update.message.text.strip().replace(',', '.'))
        product.price = str(price)
    except ValueError:
        await update.message.reply_text(
            "⚠️ Неверный формат цены. Введите число (например: 1500 или 1500.50)"
        )
        return WAITING_PRICE
    
    await update.message.reply_text(
        f"✅ Цена: {product.price} руб.\n\n"
        f"🎨 Генерирую фотореалистичное изображение модели с товаром...\n"
        f"Это займет около 30 секунд."
    )
    
    # Генерация изображения с моделью
    try:
        generated_image_url = await generate_model_photo(product)
        product.generated_image_url = generated_image_url
        
        # Отправляем сгенерированное фото (URL)
        await update.message.reply_photo(
            photo=generated_image_url,
            caption="✨ Сгенерированное фото с моделью"
        )
        
        # Показываем итоговую информацию и кнопки
        summary = (
            f"📦 **Итоговая информация о товаре:**\n\n"
            f"**Название:** {product.name}\n"
            f"**Категория:** {product.category}\n"
            f"**Цвет:** {product.color}\n"
            f"**Материал:** {product.material}\n"
            f"**Размер:** {product.size}\n"
            f"**Цена:** {product.price} руб.\n\n"
            f"**Описание:**\n{product.description}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Загрузить в магазин", callback_data="upload")],
            [InlineKeyboardButton("🔄 Изменить фото", callback_data="regenerate_photo")],
            [InlineKeyboardButton("📸 Оставить исходное фото", callback_data="use_original")],
            [InlineKeyboardButton("📝 Изменить описание", callback_data="edit_description")],
            [InlineKeyboardButton("✏️ Изменить название", callback_data="edit_name")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
        ]
        
        await update.message.reply_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return WAITING_CONFIRMATION
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при генерации фото: {str(e)[:200]}...\n"
            f"Продолжаем с исходными фото."
        )
        product.use_generated_image = False
        
        # Показываем итоговую информацию без сгенерированного фото
        summary = (
            f"📦 **Итоговая информация о товаре:**\n\n"
            f"**Название:** {product.name}\n"
            f"**Категория:** {product.category}\n"
            f"**Цвет:** {product.color}\n"
            f"**Материал:** {product.material}\n"
            f"**Размер:** {product.size}\n"
            f"**Цена:** {product.price} руб.\n\n"
            f"**Описание:**\n{product.description}"
        )
        
        keyboard = [
            [InlineKeyboardButton("✅ Загрузить в магазин", callback_data="upload")],
            [InlineKeyboardButton("📝 Изменить описание", callback_data="edit_description")],
            [InlineKeyboardButton("✏️ Изменить название", callback_data="edit_name")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
        ]
        
        await update.message.reply_text(
            summary,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return WAITING_CONFIRMATION


async def generate_model_photo(product: ProductData) -> str:
    """Генерация фотореалистичного изображения модели с товаром"""
    
    # Определяем промпт в зависимости от категории
    category_prompts = {
        "Шапка с помпоном": "wearing a hand-knitted beanie hat with a pompom",
        "Шапка слоучи": "wearing a slouchy knitted beanie hat",
        "Шапка бини": "wearing a fitted beanie hat",
        "Ушанка": "wearing a ushanka winter hat with ear flaps",
        "Шарф": "wearing a knitted scarf around her neck",
        "Платье": "wearing a knitted dress",
        "Топ": "wearing a knitted top"
    }
    
    item_description = category_prompts.get(
        product.category, 
        f"wearing a {product.category.lower()}"
    )
    
    # Используем детальное визуальное описание если есть
    visual_details = product.visual_description if product.visual_description else f"{product.color} color, made of {product.material}"
    
    prompt = f"""Ultra realistic photograph of a beautiful young woman (age 22-28) {item_description}.

EXACT PRODUCT APPEARANCE (MUST MATCH PRECISELY):
{visual_details}

Photography requirements:
- Shot on Canon EOS R5 with 85mm f/1.4 lens
- Soft natural daylight from large window
- Clean white or light grey seamless backdrop
- Shallow depth of field, subject in sharp focus
- Natural skin texture, subtle makeup, no filters
- Relaxed confident pose, genuine warm smile
- Eye contact with camera
- Professional fashion e-commerce photography
- The knitted item MUST look exactly as described above - match the colors, stripes, pattern precisely
- Real photograph quality, looks like actual photo not AI generated
- Magazine quality fashion photo"""
    
    response = openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="hd",
        n=1,
        response_format="url"
    )
    
    # Возвращаем URL изображения
    return response.data[0].url


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    product: ProductData = context.user_data.get('product')
    
    if query.data == "upload":
        await query.edit_message_text("📤 Загружаю товар в WooCommerce...")
        
        try:
            result = await upload_to_woocommerce(product)
            await query.message.reply_text(
                f"✅ Товар успешно добавлен в магазин!\n\n"
                f"🔗 ID товара: {result['id']}\n"
                f"📦 Название: {result['name']}\n"
                f"💰 Цена: {result['price']} руб.\n\n"
                f"Для добавления нового товара используйте /start"
            )
        except Exception as e:
            await query.message.reply_text(
                f"❌ Ошибка при загрузке: {str(e)[:200]}...\n\n"
                f"Попробуйте снова или начните заново /start"
            )
        
        return ConversationHandler.END
    
    elif query.data == "regenerate_photo":
        await query.edit_message_text("🎨 Генерирую новое фото...")
        
        try:
            generated_image_url = await generate_model_photo(product)
            product.generated_image_url = generated_image_url
            
            await query.message.reply_photo(
                photo=generated_image_url,
                caption="✨ Новое сгенерированное фото"
            )
            
            await query.message.reply_text(
                "✅ Новое фото готово! Выберите действие:",
                reply_markup=query.message.reply_markup
            )
        except Exception as e:
            await query.message.reply_text(
                f"❌ Ошибка при регенерации: {str(e)[:200]}"
            )
        
        return WAITING_CONFIRMATION
    
    elif query.data == "use_original":
        product.use_generated_image = False
        await query.edit_message_text(
            "✅ Будут использованы исходные фотографии.\n\n"
            "Выберите действие:"
        )
        # Показываем кнопки снова
        keyboard = [
            [InlineKeyboardButton("✅ Загрузить в магазин", callback_data="upload")],
            [InlineKeyboardButton("🔄 Изменить фото", callback_data="regenerate_photo")],
            [InlineKeyboardButton("📝 Изменить описание", callback_data="edit_description")],
            [InlineKeyboardButton("✏️ Изменить название", callback_data="edit_name")],
            [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
        ]
        await query.message.reply_text(
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_CONFIRMATION
    
    elif query.data == "edit_description":
        await query.edit_message_text(
            "📝 Отправьте новое описание товара:"
        )
        context.user_data['editing'] = 'description'
        return WAITING_CONFIRMATION
    
    elif query.data == "edit_name":
        await query.edit_message_text(
            "✏️ Отправьте новое название товара:"
        )
        context.user_data['editing'] = 'name'
        return WAITING_CONFIRMATION
    
    elif query.data == "cancel":
        await query.edit_message_text(
            "❌ Операция отменена.\n\n"
            "Для начала работы используйте /start"
        )
        return ConversationHandler.END


async def edit_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка редактирования текстовых полей"""
    product: ProductData = context.user_data.get('product')
    editing = context.user_data.get('editing')
    
    if editing == 'description':
        product.description = update.message.text.strip()
        await update.message.reply_text(
            f"✅ Описание обновлено:\n\n{product.description}"
        )
    elif editing == 'name':
        product.name = update.message.text.strip()
        await update.message.reply_text(
            f"✅ Название обновлено: {product.name}"
        )
    
    context.user_data.pop('editing', None)
    
    # Показываем кнопки снова
    keyboard = [
        [InlineKeyboardButton("✅ Загрузить в магазин", callback_data="upload")],
        [InlineKeyboardButton("🔄 Изменить фото", callback_data="regenerate_photo")],
        [InlineKeyboardButton("📸 Оставить исходное фото", callback_data="use_original")],
        [InlineKeyboardButton("📝 Изменить описание", callback_data="edit_description")],
        [InlineKeyboardButton("✏️ Изменить название", callback_data="edit_name")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel")]
    ]
    
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return WAITING_CONFIRMATION


async def get_or_create_category(category_name: str) -> int:
    """Получение ID категории или создание новой"""
    # Ищем существующую категорию
    response = wcapi.get("products/categories", params={"search": category_name})
    if response.status_code == 200:
        categories = response.json()
        for cat in categories:
            if cat['name'].lower() == category_name.lower():
                return cat['id']
    
    # Создаем новую категорию
    response = wcapi.post("products/categories", {"name": category_name})
    if response.status_code in [200, 201]:
        return response.json()['id']
    
    return None


async def upload_to_woocommerce(product: ProductData) -> Dict:
    """Загрузка товара в WooCommerce"""

    # Проверяем настройки WordPress Media API
    wp_username = os.getenv('WP_USERNAME')
    wp_app_password = os.getenv('WP_APP_PASSWORD')
    wp_url = os.getenv('WC_URL')

    uploaded_images = []

    # Если настроены учётные данные WordPress, загружаем через Media Library
    if wp_username and wp_app_password:
        print("📤 Используется загрузка через WordPress Media Library")
        from media_uploader import upload_images_batch

        # Собираем URL изображений
        image_urls = []
        if product.use_generated_image and product.generated_image_url:
            image_urls.append(product.generated_image_url)
        image_urls.extend(product.photo_urls[:2])

        # Ограничиваем до 3 изображений
        image_urls = image_urls[:3]

        # Загружаем изображения через Media Library
        uploaded_images = upload_images_batch(
            image_urls,
            wp_url,
            wp_username,
            wp_app_password
        )

        if not uploaded_images:
            print("⚠️ Не удалось загрузить изображения через Media Library")
            print("⚠️ Товар будет создан без изображений")

    else:
        print("⚠️ WP_USERNAME или WP_APP_PASSWORD не настроены")
        print("⚠️ Товар будет создан без изображений")
        print("💡 См. SETUP_MEDIA_UPLOAD.md для настройки загрузки изображений")
    
    # Получаем или создаем категорию
    category_id = await get_or_create_category(product.category)
    categories_data = [{"id": category_id}] if category_id else []
    
    # Создаем товар в WooCommerce
    product_data = {
        "name": product.name,
        "type": "simple",
        "regular_price": product.price,
        "description": product.description,
        "short_description": f"{product.category} из {product.material}. Размер: {product.size}. Цвет: {product.color}.",
        "categories": categories_data,
        "images": uploaded_images,
        "attributes": [
            {
                "name": "Цвет",
                "options": [product.color],
                "visible": True
            },
            {
                "name": "Материал",
                "options": [product.material],
                "visible": True
            },
            {
                "name": "Размер",
                "options": [product.size],
                "visible": True
            }
        ],
        "meta_data": [
            {
                "key": "_ai_generated",
                "value": "true"
            },
            {
                "key": "_generation_date",
                "value": datetime.now().isoformat()
            }
        ]
    }
    
    print(f"Отправка товара в WooCommerce: {product.name}")
    print(f"Количество изображений для загрузки: {len(uploaded_images)}")

    # Отправляем запрос в WooCommerce
    response = wcapi.post("products", product_data)

    if response.status_code not in [200, 201]:
        error_text = response.text
        print(f"WooCommerce API error (status {response.status_code}): {error_text}")
        raise Exception(f"WooCommerce API error (status {response.status_code}): {error_text[:500]}")

    print(f"✅ Товар успешно создан: ID {response.json().get('id')}")
    return response.json()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции"""
    await update.message.reply_text(
        "❌ Операция отменена.\n\n"
        "Для начала работы используйте /start"
    )
    return ConversationHandler.END


def main():
    """Запуск бота"""
    # Получаем токен бота
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ Ошибка: не установлен TELEGRAM_BOT_TOKEN")
        return
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_PHOTOS: [
                MessageHandler(filters.PHOTO, receive_photo),
                CommandHandler("done", photos_done)
            ],
            WAITING_MATERIAL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_material)
            ],
            WAITING_SIZE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_size)
            ],
            WAITING_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_price)
            ],
            WAITING_CONFIRMATION: [
                CallbackQueryHandler(button_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_text_handler)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    application.add_handler(conv_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
