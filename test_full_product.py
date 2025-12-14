#!/usr/bin/env python3
"""
Полный тест создания товара с изображениями через Media Library.

При запуске через pytest тест пропускается, если отсутствуют зависимости
или обязательные переменные окружения. При запуске как скрипт выполняется
полный интеграционный сценарий с очисткой тестовых данных.
"""
import os

import pytest
from dotenv import load_dotenv

woocommerce = pytest.importorskip("woocommerce")
from woocommerce import API

from media_uploader import upload_images_batch


load_dotenv()


def _has_required_env():
    return all(
        [
            os.getenv("WC_URL"),
            os.getenv("WC_KEY"),
            os.getenv("WC_SECRET"),
            os.getenv("WP_USERNAME"),
            os.getenv("WP_APP_PASSWORD"),
        ]
    )


def _create_wc_api():
    return API(
        url=os.getenv("WC_URL"),
        consumer_key=os.getenv("WC_KEY"),
        consumer_secret=os.getenv("WC_SECRET"),
        version=os.getenv("WC_VERSION", "wc/v3"),
        timeout=120,
    )


def _delete_uploaded_images(uploaded_images):
    import requests

    print(f"\n🧹 Шаг 4: Удаление изображений из Media Library...")
    print("-" * 70)
    for img in uploaded_images:
        delete_url = f"{os.getenv('WC_URL')}/wp-json/wp/v2/media/{img['id']}"
        delete_resp = requests.delete(
            delete_url,
            auth=(os.getenv("WP_USERNAME"), os.getenv("WP_APP_PASSWORD")),
            params={"force": True},
            timeout=30,
        )
        if delete_resp.status_code == 200:
            print(f"✅ Изображение удалено (ID: {img['id']})")
        else:
            print(f"⚠️ Не удалось удалить изображение (ID: {img['id']})")


def run_full_product_flow():
    print("=" * 70)
    print("ПОЛНЫЙ ТЕСТ: Создание товара с изображениями")
    print("=" * 70)

    test_images = [
        "https://picsum.photos/800/600?random=1",
        "https://picsum.photos/800/600?random=2",
    ]

    print(f"\n📤 Шаг 1: Загрузка {len(test_images)} изображений в Media Library...")
    print("-" * 70)

    uploaded_images = upload_images_batch(
        test_images,
        os.getenv("WC_URL"),
        os.getenv("WP_USERNAME"),
        os.getenv("WP_APP_PASSWORD"),
    )

    if not uploaded_images:
        print("❌ Не удалось загрузить изображения. Тест прерван.")
        return False

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
            {"name": "Цвет", "options": ["Бордовый"], "visible": True},
            {"name": "Материал", "options": ["Шерсть"], "visible": True},
            {"name": "Размер", "options": ["Универсальный"], "visible": True},
        ],
    }

    wcapi = _create_wc_api()

    try:
        response = wcapi.post("products", product_data)

        if response.status_code in [200, 201]:
            product = response.json()
            print(f"✅ УСПЕХ! Товар создан")
            print(f"   ID товара: {product['id']}")
            print(f"   Название: {product['name']}")
            print(f"   Цена: {product['regular_price']} руб.")
            print(f"   Изображений: {len(product.get('images', []))}")

            if product.get("images"):
                print(f"\n   📸 Изображения товара:")
                for idx, img in enumerate(product["images"]):
                    print(f"      {idx + 1}. {img.get('src', 'N/A')}")

            product_id = product["id"]

            print(f"\n🧹 Шаг 3: Удаление тестового товара...")
            print("-" * 70)
            delete_response = wcapi.delete(f"products/{product_id}", params={"force": True})
            if delete_response.status_code == 200:
                print(f"✅ Тестовый товар удалён (ID: {product_id})")
            else:
                print(f"⚠️ Не удалось удалить товар (ID: {product_id})")

            _delete_uploaded_images(uploaded_images)
        else:
            print(f"❌ ОШИБКА при создании товара: {response.status_code}")
            print(f"   {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        return False

    print("\n" + "=" * 70)
    print("ТЕСТ ЗАВЕРШЁН!")
    print("=" * 70)
    print("\n🎉 Если все шаги успешны, бот готов к работе!")
    print("   Запустите: python3 bot.py")
    return True


def test_full_product_flow():
    if not _has_required_env():
        pytest.skip("Не заданы переменные окружения для WooCommerce/WordPress — пропускаем интеграционный тест.")

    assert run_full_product_flow(), "Интеграционный сценарий создания товара завершился с ошибкой"


if __name__ == "__main__":
    if not _has_required_env():
        print("❌ Не заданы переменные окружения WC_URL/WC_KEY/WC_SECRET/WP_USERNAME/WP_APP_PASSWORD")
        exit(1)
    run_full_product_flow()
