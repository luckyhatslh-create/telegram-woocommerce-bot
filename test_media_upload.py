#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки в WordPress Media Library.

Поведение при запуске зависит от окружения:
- При запуске через pytest тест пропускается, если не заданы WP_USERNAME или
  WP_APP_PASSWORD.
- При запуске как самостоятельный скрипт выводятся подробные подсказки и
  очищается тестовый медиафайл после успешной загрузки.
"""
import base64
import os

import pytest
from dotenv import load_dotenv

from media_uploader import upload_image_to_media


load_dotenv()


def _get_wp_credentials():
    """Возвращает URL, логин и пароль приложения WordPress из окружения."""

    wp_url = os.getenv("WC_URL")
    wp_username = os.getenv("WP_USERNAME")
    wp_app_password = os.getenv("WP_APP_PASSWORD")
    return wp_url, wp_username, wp_app_password


def _get_test_image_bytes():
    """Создаёт тестовое 1x1 JPEG изображение в байтах."""

    pixel_b64 = (
        "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBI"
        "UFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDAREAAhEBAxEB/8QAHwA"
        "AAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJic"
        "oKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uH"
        "i4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEK"
        "RobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO"
        "0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9Sq//2Q=="
    )
    return base64.b64decode(pixel_b64)


def _delete_media_file(wp_url: str, wp_username: str, wp_app_password: str, media_id: int) -> bool:
    """Удаляет тестовый медиафайл. Возвращает True при успехе."""

    import requests

    delete_url = f"{wp_url}/wp-json/wp/v2/media/{media_id}"
    delete_response = requests.delete(
        delete_url,
        auth=(wp_username, wp_app_password),
        params={"force": True},
        timeout=30,
    )
    return delete_response.status_code == 200


def _run_media_upload():
    """Выполняет загрузку тестового изображения и возвращает результат."""

    wp_url, wp_username, wp_app_password = _get_wp_credentials()

    if not wp_username or not wp_app_password:
        return None

    return upload_image_to_media(
        image_data=_get_test_image_bytes(),
        filename="test_pixel_from_bot.jpg",
        wp_url=wp_url,
        wp_username=wp_username,
        wp_app_password=wp_app_password,
    )


def test_media_upload_configuration():
    """Пропускает тест без учётных данных и проверяет загрузку при наличии."""

    wp_url, wp_username, wp_app_password = _get_wp_credentials()
    if not wp_username or not wp_app_password:
        pytest.skip("WP_USERNAME/WP_APP_PASSWORD не заданы — пропускаем тест загрузки медиа.")

    result = _run_media_upload()

    assert result, "Не удалось загрузить изображение в Media Library"
    assert "id" in result and "url" in result and "title" in result, "Ответ Media Library не содержит ожидаемых полей"

    assert _delete_media_file(wp_url, wp_username, wp_app_password, result["id"]), "Не удалось удалить тестовый медиафайл"


def _print_header():
    print("=" * 70)
    print("Тест загрузки изображения в WordPress Media Library")
    print("=" * 70)


def _print_missing_credentials_help():
    print("\n❌ ОШИБКА: Не заданы WP_USERNAME или WP_APP_PASSWORD")
    print("\n📋 Инструкция по настройке:")
    print("1. Откройте файл SETUP_MEDIA_UPLOAD.md")
    print("2. Следуйте инструкциям для создания Application Password")
    print("3. Добавьте WP_USERNAME и WP_APP_PASSWORD в файл .env")
    print("\nПример .env:")
    print("WP_USERNAME=admin")
    print("WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx")


def _run_manual_script():
    _print_header()
    wp_url, wp_username, wp_app_password = _get_wp_credentials()

    if not wp_username or not wp_app_password:
        _print_missing_credentials_help()
        return

    print("\n📋 Конфигурация:")
    print(f"   WordPress URL: {wp_url}")
    print(f"   Пользователь: {wp_username}")
    print(f"   Пароль приложения: {'*' * len(wp_app_password)}")

    print("\n📤 Загружаем тестовое изображение...")
    print("-" * 70)

    result = _run_media_upload()
    if result:
        print("✅ УСПЕХ! Изображение загружено в Media Library")
        print(f"   ID медиафайла: {result['id']}")
        print(f"   URL: {result['url']}")
        print(f"   Название: {result['title']}")
        print("\n🎉 Всё настроено правильно! Теперь бот сможет загружать изображения.")

        print("\n🧹 Очистка: Удаляем тестовое изображение...")
        if _delete_media_file(wp_url, wp_username, wp_app_password, result["id"]):
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


if __name__ == "__main__":
    _run_manual_script()
