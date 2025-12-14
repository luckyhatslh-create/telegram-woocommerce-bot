#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки товара в WooCommerce.

При запуске через pytest пропускается без обязательных переменных окружения
или установленного модуля woocommerce. При запуске как скрипт выполняет
интеграционные проверки с очисткой тестовых товаров.
"""
import os
import base64

import pytest
from dotenv import load_dotenv

woocommerce = pytest.importorskip("woocommerce")
from woocommerce import API


load_dotenv()


def _has_required_env():
    return all([os.getenv("WC_URL"), os.getenv("WC_KEY"), os.getenv("WC_SECRET")])


def _create_wc_api():
    return API(
        url=os.getenv("WC_URL"),
        consumer_key=os.getenv("WC_KEY"),
        consumer_secret=os.getenv("WC_SECRET"),
        version=os.getenv("WC_VERSION", "wc/v3"),
        timeout=120,
    )


def run_product_tests():
    print("=" * 60)
    print("Тест загрузки товара в WooCommerce")
    print("=" * 60)

    pixel_b64 = (
        "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBI"
        "UFRT/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT/wAARCAABAAEDAREAAhEBAxEB/8QAHwA"
        "AAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJic"
        "oKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uH"
        "i4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEK"
        "RobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO"
        "0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD9Sq//2Q=="
    )

    wcapi = _create_wc_api()

    print("\n🧪 Тест 1: Создание товара БЕЗ изображений")
    print("-" * 60)

    product_data_no_images = {
        "name": "Тестовый товар (без изображений)",
        "type": "simple",
        "regular_price": "1000",
        "description": "Это тестовый товар для проверки работы API",
        "short_description": "Тестовый товар",
        "status": "draft",
    }

    try:
        response = wcapi.post("products", product_data_no_images)
        if response.status_code in [200, 201]:
            product = response.json()
            print(f"✅ УСПЕХ! Товар создан")
            print(f"   ID: {product['id']}")
            print(f"   Название: {product['name']}")
            print(f"   Цена: {product['regular_price']} руб.")
            test1_product_id = product["id"]
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            print(f"   {response.text[:300]}")
            test1_product_id = None
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        test1_product_id = None

    print("\n🧪 Тест 2: Создание товара С изображением (base64)")
    print("-" * 60)

    product_data_with_image = {
        "name": "Тестовый товар (с изображением base64)",
        "type": "simple",
        "regular_price": "1500",
        "description": "Это тестовый товар с изображением в base64",
        "short_description": "Тестовый товар с изображением",
        "status": "draft",
        "images": [{"src": f"data:image/jpeg;base64,{pixel_b64}", "name": "test_image.jpg"}],
    }

    try:
        response = wcapi.post("products", product_data_with_image)
        if response.status_code in [200, 201]:
            product = response.json()
            print(f"✅ УСПЕХ! Товар с изображением создан")
            print(f"   ID: {product['id']}")
            print(f"   Название: {product['name']}")
            print(f"   Количество изображений: {len(product.get('images', []))}")
            test2_product_id = product["id"]
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            print(f"   {response.text[:500]}")
            test2_product_id = None
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        test2_product_id = None

    print("\n🧪 Тест 3: Проверка системных настроек WooCommerce")
    print("-" * 60)

    try:
        response = wcapi.get("system_status")
        if response.status_code == 200:
            system = response.json()
            print(f"✅ Доступ к системным настройкам получен")
            print(f"   WooCommerce версия: {system.get('environment', {}).get('version', 'N/A')}")
            print(f"   WordPress версия: {system.get('environment', {}).get('wp_version', 'N/A')}")
        else:
            print(f"⚠️ Не удалось получить системные настройки: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Ошибка при получении настроек: {e}")

    print("\n🧹 Очистка: Удаление тестовых товаров")
    print("-" * 60)

    for product_id in [test1_product_id, test2_product_id]:
        if product_id:
            try:
                response = wcapi.delete(f"products/{product_id}", params={"force": True})
                if response.status_code == 200:
                    print(f"✅ Товар ID {product_id} удалён")
                else:
                    print(f"⚠️ Не удалось удалить товар ID {product_id}")
            except Exception as e:
                print(f"⚠️ Ошибка при удалении товара ID {product_id}: {e}")

    print("\n" + "=" * 60)
    print("Тестирование завершено!")
    print("=" * 60)

    return bool(test1_product_id)


def test_woocommerce_product_flow():
    if not _has_required_env():
        pytest.skip("Не заданы переменные окружения для WooCommerce — пропускаем интеграционный тест товаров.")

    assert run_product_tests(), "Интеграционный тест создания товаров завершился с ошибкой"


if __name__ == "__main__":
    if not _has_required_env():
        print("❌ Не заданы переменные окружения WC_URL/WC_KEY/WC_SECRET")
        exit(1)
    run_product_tests()
