#!/usr/bin/env python3
"""
Тест загрузки товара в WooCommerce с изображением по URL.

При выполнении через pytest тест пропускается, если не заданы обязательные
переменные окружения или недоступен модуль woocommerce. При запуске как
скрипт выполняется интеграционный сценарий создания и удаления товара.
"""
import os

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


def run_url_upload_test():
    print("=" * 70)
    print("Тест загрузки товара с изображением по прямому URL")
    print("=" * 70)

    test_image_url = "https://picsum.photos/800/600"

    product_data = {
        "name": "Тестовый товар (изображение по URL)",
        "type": "simple",
        "regular_price": "1500",
        "description": "Тестовый товар с изображением загруженным по прямому URL",
        "short_description": "Тест с URL изображением",
        "status": "draft",
        "images": [{"src": test_image_url, "name": "test_image_from_url.jpg"}],
    }

    print(f"\n📤 Загружаем товар с изображением из: {test_image_url}")
    print("-" * 70)

    wcapi = _create_wc_api()

    try:
        response = wcapi.post("products", product_data)

        if response.status_code in [200, 201]:
            product = response.json()
            print(f"✅ УСПЕХ! Товар создан")
            print(f"   ID: {product['id']}")
            print(f"   Название: {product['name']}")
            print(f"   Цена: {product['regular_price']} руб.")
            print(f"   Количество изображений: {len(product.get('images', []))}")

            if product.get("images"):
                print(f"   URL изображения: {product['images'][0].get('src', 'N/A')}")

            print(f"\n🧹 Удаляем тестовый товар...")
            delete_response = wcapi.delete(f"products/{product['id']}", params={"force": True})
            if delete_response.status_code == 200:
                print(f"✅ Тестовый товар удалён")
            else:
                print(f"⚠️ Не удалось удалить тестовый товар (ID: {product['id']})")
        else:
            print(f"❌ ОШИБКА: {response.status_code}")
            print(f"   {response.text[:700]}")
            return False

    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

    print("\n" + "=" * 70)
    print("Тестирование завершено!")
    print("=" * 70)
    print("\n💡 Если тест успешен, значит WooCommerce может загружать изображения по URL")
    print("   Telegram URL работают только в течение 1 часа после отправки файла!")
    return True


def test_url_upload_flow():
    if not _has_required_env():
        pytest.skip("Не заданы переменные окружения для WooCommerce — пропускаем тест загрузки товара по URL.")

    assert run_url_upload_test(), "Создание товара по URL завершилось с ошибкой"


if __name__ == "__main__":
    if not _has_required_env():
        print("❌ Не заданы переменные окружения WC_URL/WC_KEY/WC_SECRET")
        exit(1)
    run_url_upload_test()
