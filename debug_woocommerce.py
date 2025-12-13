#!/usr/bin/env python3
"""
Детальная диагностика подключения к WooCommerce API
"""
import os
from dotenv import load_dotenv
from woocommerce import API

load_dotenv()

url = os.getenv('WC_URL', '')
key = os.getenv('WC_KEY', '')
secret = os.getenv('WC_SECRET', '')
version = os.getenv('WC_VERSION', 'wc/v3')

print("=" * 70)
print("ДИАГНОСТИКА WOOCOMMERCE API")
print("=" * 70)

print("\n📋 Проверка переменных окружения:")
print(f"   WC_URL: {url[:30]}{'...' if len(url) > 30 else ''}")
print(f"   WC_KEY: {key[:10]}... (длина: {len(key)})")
print(f"   WC_SECRET: {secret[:10]}... (длина: {len(secret)})")
print(f"   WC_VERSION: {version}")

if not url:
    print("\n❌ WC_URL не установлен!")
    exit(1)

if not key or not key.startswith('ck_'):
    print(f"\n⚠️ WC_KEY должен начинаться с 'ck_', текущее значение: {key[:10]}...")

if not secret or not secret.startswith('cs_'):
    print(f"\n⚠️ WC_SECRET должен начинаться с 'cs_', текущее значение: {secret[:10]}...")

# Проверка URL
if url.endswith('/'):
    print(f"\n⚠️ WC_URL не должен заканчиваться на '/', текущее: {url}")

print("\n🔌 Попытка подключения к WooCommerce API...")

try:
    wcapi = API(
        url=url,
        consumer_key=key,
        consumer_secret=secret,
        version=version,
        timeout=30
    )

    print(f"\n1️⃣ Тест: Получение списка товаров (products)")
    print("-" * 70)
    response = wcapi.get("products", params={"per_page": 1})
    print(f"   Статус: {response.status_code}")
    if response.status_code == 200:
        products = response.json()
        print(f"   ✅ Успешно! Найдено товаров: {len(products)}")
    else:
        print(f"   ❌ Ошибка: {response.text[:200]}")

    print(f"\n2️⃣ Тест: Получение системного статуса (system_status)")
    print("-" * 70)
    response = wcapi.get("system_status")
    print(f"   Статус: {response.status_code}")
    if response.status_code == 200:
        system = response.json()
        print(f"   ✅ Успешно!")
        env = system.get('environment', {})
        print(f"   WooCommerce версия: {env.get('version', 'N/A')}")
        print(f"   WordPress версия: {env.get('wp_version', 'N/A')}")
    else:
        print(f"   ❌ Ошибка: {response.text[:200]}")

    print(f"\n3️⃣ Тест: Получение настроек (settings/general)")
    print("-" * 70)
    response = wcapi.get("settings/general")
    print(f"   Статус: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Успешно!")
    else:
        print(f"   ❌ Ошибка: {response.text[:200]}")

except Exception as e:
    print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("РЕКОМЕНДАЦИИ ПО УСТРАНЕНИЮ ОШИБКИ 401:")
print("=" * 70)
print("""
1. В WordPress админке перейдите: WooCommerce → Настройки → Дополнительно → REST API
2. Удалите старые ключи и создайте НОВЫЙ ключ
3. Убедитесь, что права установлены: Чтение/Запись (Read/Write)
4. Скопируйте Consumer key и Consumer secret
5. Обновите .env файл:
   WC_KEY=ck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   WC_SECRET=cs_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
6. WC_URL должен быть БЕЗ завершающего слеша:
   ✅ Правильно: https://yourstore.com
   ❌ Неправильно: https://yourstore.com/
""")
