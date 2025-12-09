#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки в WordPress Media Library
"""
import os
import base64
from dotenv import load_dotenv
from media_uploader import upload_image_to_media

load_dotenv()

print("=" * 70)
print("Тест загрузки изображения в WordPress Media Library")
print("=" * 70)

# Проверяем наличие необходимых переменных окружения
wp_url = os.getenv('WC_URL')
wp_username = os.getenv('WP_USERNAME')
wp_app_password = os.getenv('WP_APP_PASSWORD')

if not wp_username or not wp_app_password:
    print("\n❌ ОШИБКА: Не заданы WP_USERNAME или WP_APP_PASSWORD")
    print("\n📋 Инструкция по настройке:")
    print("1. Откройте файл SETUP_MEDIA_UPLOAD.md")
    print("2. Следуйте инструкциям для создания Application Password")
    print("3. Добавьте WP_USERNAME и WP_APP_PASSWORD в файл .env")
    print("\nПример .env:")
    print("WP_USERNAME=admin")
    print("WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx")
    exit(1)

print(f"\n📋 Конфигурация:")
print(f"   WordPress URL: {wp_url}")
print(f"   Пользователь: {wp_username}")
print(f"   Пароль приложения: {'*' * len(wp_app_password)}")

# Создаём тестовое изображение (1x1 чёрный пиксель JPEG)
pixel_b64 = "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDAREAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9Sq//2Q=="
test_image_data = base64.b64decode(pixel_b64)

print("\n📤 Загружаем тестовое изображение...")
print("-" * 70)

result = upload_image_to_media(
    image_data=test_image_data,
    filename="test_pixel_from_bot.jpg",
    wp_url=wp_url,
    wp_username=wp_username,
    wp_app_password=wp_app_password
)

if result:
    print(f"✅ УСПЕХ! Изображение загружено в Media Library")
    print(f"   ID медиафайла: {result['id']}")
    print(f"   URL: {result['url']}")
    print(f"   Название: {result['title']}")
    print("\n🎉 Всё настроено правильно! Теперь бот сможет загружать изображения.")

    # Удаляем тестовое изображение
    print("\n🧹 Очистка: Удаляем тестовое изображение...")
    import requests
    delete_url = f"{wp_url}/wp-json/wp/v2/media/{result['id']}"
    delete_response = requests.delete(
        delete_url,
        auth=(wp_username, wp_app_password),
        params={"force": True},
        timeout=30
    )
    if delete_response.status_code == 200:
        print("✅ Тестовое изображение удалено")
    else:
        print(f"⚠️ Тестовое изображение осталось в Media Library (ID: {result['id']})")

else:
    print(f"❌ ОШИБКА: Не удалось загрузить изображение")
    print("\n🔍 Возможные причины:")
    print("1. Неправильный логин или пароль приложения")
    print("2. Application Password не активирован на сайте")
    print("3. Проблемы с правами доступа пользователя")
    print("\n💡 Проверьте:")
    print("- Правильность логина (обычно это 'admin' или email)")
    print("- Что пароль приложения без пробелов")
    print("- Что пользователь имеет права на загрузку файлов")

print("\n" + "=" * 70)
print("Тестирование завершено!")
print("=" * 70)
