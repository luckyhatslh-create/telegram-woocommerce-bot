#!/usr/bin/env python3
"""
Полный тест создания товара с изображениями через Media Library
"""
import os
import asyncio
from dotenv import load_dotenv
from woocommerce import API
from media_uploader import upload_images_batch

load_dotenv()

# Инициализация WooCommerce API
wcapi = API(
    url=os.getenv('WC_URL'),
    consumer_key=os.getenv('WC_KEY'),
    consumer_secret=os.getenv('WC_SECRET'),
    version="wc/v3",
    timeout=120
)

print("=" * 70)
print("ПОЛНЫЙ ТЕСТ: Создание товара с изображениями")
print("=" * 70)

# Используем публичное тестовое изображение
test_images = [
    "https://picsum.photos/800/600?random=1",
    "https://picsum.photos/800/600?random=2"
]

print(f"\n📤 Шаг 1: Загрузка {len(test_images)} изображений в Media Library...")
print("-" * 70)

uploaded_images = upload_images_batch(
    test_images,
    os.getenv('WC_URL'),
    os.getenv('WP_USERNAME'),
    os.getenv('WP_APP_PASSWORD')
)

if not uploaded_images:
    print("❌ Не удалось загрузить изображения. Тест прерван.")
    exit(1)

print(f"\n✅ Загружено изображений: {len(uploaded_images)}")
for idx, img in enumerate(uploaded_images):
    print(f"   Изображение {idx + 1}: ID {img['id']}")

print(f"\n📦 Шаг 2: Создание товара в WooCommerce...")
print("-" * 70)

product_data = {
    "name": "Тестовая шапка с помпоном",
    "type": "simple",
    "regular_price": "1500",
    "description": "Вязаная шапка ручной работы с помпоном. Создано через Telegram бота.",
    "short_description": "Вязаная шапка с помпоном",
    "status": "draft",
    "images": uploaded_images,
    "categories": [],
    "attributes": [
        {
            "name": "Цвет",
            "options": ["Бордовый"],
            "visible": True
        },
        {
            "name": "Материал",
            "options": ["Шерсть"],
            "visible": True
        },
        {
            "name": "Размер",
            "options": ["Универсальный"],
            "visible": True
        }
    ]
}

try:
    response = wcapi.post("products", product_data)

    if response.status_code in [200, 201]:
        product = response.json()
        print(f"✅ УСПЕХ! Товар создан")
        print(f"   ID товара: {product['id']}")
        print(f"   Название: {product['name']}")
        print(f"   Цена: {product['regular_price']} руб.")
        print(f"   Изображений: {len(product.get('images', []))}")

        if product.get('images'):
            print(f"\n   📸 Изображения товара:")
            for idx, img in enumerate(product['images']):
                print(f"      {idx + 1}. {img.get('src', 'N/A')}")

        product_id = product['id']

        # Удаляем тестовый товар
        print(f"\n🧹 Шаг 3: Удаление тестового товара...")
        print("-" * 70)
        delete_response = wcapi.delete(f"products/{product_id}", params={"force": True})
        if delete_response.status_code == 200:
            print(f"✅ Тестовый товар удалён (ID: {product_id})")
        else:
            print(f"⚠️ Не удалось удалить товар (ID: {product_id})")

        # Удаляем изображения из Media Library
        print(f"\n🧹 Шаг 4: Удаление изображений из Media Library...")
        print("-" * 70)
        import requests
        for img in uploaded_images:
            delete_url = f"{os.getenv('WC_URL')}/wp-json/wp/v2/media/{img['id']}"
            delete_resp = requests.delete(
                delete_url,
                auth=(os.getenv('WP_USERNAME'), os.getenv('WP_APP_PASSWORD')),
                params={"force": True},
                timeout=30
            )
            if delete_resp.status_code == 200:
                print(f"✅ Изображение удалено (ID: {img['id']})")
            else:
                print(f"⚠️ Не удалось удалить изображение (ID: {img['id']})")

    else:
        print(f"❌ ОШИБКА при создании товара: {response.status_code}")
        print(f"   {response.text[:500]}")

except Exception as e:
    print(f"❌ ИСКЛЮЧЕНИЕ: {e}")

print("\n" + "=" * 70)
print("ТЕСТ ЗАВЕРШЁН!")
print("=" * 70)
print("\n🎉 Если все шаги успешны, бот готов к работе!")
print("   Запустите: python3 bot.py")
