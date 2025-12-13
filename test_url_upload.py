#!/usr/bin/env python3
"""
Тест загрузки товара в WooCommerce с изображением по URL
"""
import os
from dotenv import load_dotenv
from woocommerce import API

load_dotenv()

wcapi = API(
    url=os.getenv('WC_URL'),
    consumer_key=os.getenv('WC_KEY'),
    consumer_secret=os.getenv('WC_SECRET'),
    version=os.getenv('WC_VERSION', 'wc/v3'),
    timeout=120
)

print("=" * 70)
print("Тест загрузки товара с изображением по прямому URL")
print("=" * 70)

# Используем публичное тестовое изображение
test_image_url = "https://picsum.photos/800/600"

product_data = {
    "name": "Тестовый товар (изображение по URL)",
    "type": "simple",
    "regular_price": "1500",
    "description": "Тестовый товар с изображением загруженным по прямому URL",
    "short_description": "Тест с URL изображением",
    "status": "draft",
    "images": [
        {
            "src": test_image_url,
            "name": "test_image_from_url.jpg"
        }
    ]
}

print(f"\n📤 Загружаем товар с изображением из: {test_image_url}")
print("-" * 70)

try:
    response = wcapi.post("products", product_data)

    if response.status_code in [200, 201]:
        product = response.json()
        print(f"✅ УСПЕХ! Товар создан")
        print(f"   ID: {product['id']}")
        print(f"   Название: {product['name']}")
        print(f"   Цена: {product['regular_price']} руб.")
        print(f"   Количество изображений: {len(product.get('images', []))}")

        if product.get('images'):
            print(f"   URL изображения: {product['images'][0].get('src', 'N/A')}")

        # Удаляем тестовый товар
        print(f"\n🧹 Удаляем тестовый товар...")
        delete_response = wcapi.delete(f"products/{product['id']}", params={"force": True})
        if delete_response.status_code == 200:
            print(f"✅ Тестовый товар удалён")
        else:
            print(f"⚠️ Не удалось удалить тестовый товар (ID: {product['id']})")

    else:
        print(f"❌ ОШИБКА: {response.status_code}")
        print(f"   {response.text[:700]}")

except Exception as e:
    print(f"❌ ИСКЛЮЧЕНИЕ: {e}")

print("\n" + "=" * 70)
print("Тестирование завершено!")
print("=" * 70)
print("\n💡 Если тест успешен, значит WooCommerce может загружать изображения по URL")
print("   Telegram URL работают только в течение 1 часа после отправки файла!")
