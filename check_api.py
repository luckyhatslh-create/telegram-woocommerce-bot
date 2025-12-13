"""Скрипт для проверки подключения к API сервисам"""
import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()


def check_telegram():
    """Проверка Telegram Bot Token"""
    print("🔍 Проверка Telegram Bot...")
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не установлен в .env")
        return False

    try:
        import requests
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=15)
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Telegram Bot подключен: @{bot_info['result']['username']}")
            return True
        else:
            print(f"❌ Ошибка подключения к Telegram: {response.status_code}")
            return False
    except Exception as e:  # noqa: BLE001
        print(f"❌ Ошибка: {e}")
        return False


def check_anthropic():
    """Проверка Anthropic API"""
    print("\n🔍 Проверка Anthropic API...")
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print("❌ ANTHROPIC_API_KEY не установлен в .env")
        return False

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        print(f"✅ Anthropic доступен, модель: {message.model}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"❌ Ошибка Anthropic: {e}")
        return False


def check_replicate():
    """Проверка Replicate API"""
    print("\n🔍 Проверка Replicate API...")
    token = os.getenv('REPLICATE_API_TOKEN')
    if not token:
        print("❌ REPLICATE_API_TOKEN не установлен в .env")
        return False
    try:
        import replicate

        client = replicate.Client(api_token=token)
        client.models.list()  # лёгкий вызов для проверки токена
        print("✅ Replicate токен принят")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"❌ Ошибка Replicate: {e}")
        return False


def check_woocommerce():
    """Проверка WooCommerce API"""
    print("\n🔍 Проверка WooCommerce API...")

    url = os.getenv('WC_URL')
    key = os.getenv('WC_KEY')
    secret = os.getenv('WC_SECRET')

    if not all([url, key, secret]):
        print("⚠️ WooCommerce credentials не установлены в .env (можно пропустить, если не используется)")
        return False

    try:
        from woocommerce import API

        wcapi = API(
            url=url,
            consumer_key=key,
            consumer_secret=secret,
            version="wc/v3",
            timeout=10
        )

        response = wcapi.get("system_status")

        if response.status_code == 200:
            print(f"✅ WooCommerce API подключен")
            return True
        else:
            print(f"❌ Ошибка подключения: {response.status_code}")
            print(f"   {response.text}")
            return False

    except Exception as e:  # noqa: BLE001
        print(f"❌ Ошибка: {e}")
        return False


def main():
    """Главная функция"""
    print("=" * 60)
    print("🔧 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К API СЕРВИСАМ")
    print("=" * 60)

    if not os.path.exists('.env'):
        print("\n⚠️ Файл .env не найден. Создайте его или задайте переменные окружения.")

    results = {
        'Telegram': check_telegram(),
        'Anthropic': check_anthropic(),
        'Replicate': check_replicate(),
        'WooCommerce (опционально)': check_woocommerce(),
    }

    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
    print("=" * 60)

    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'Подключен' if status else 'Ошибка'}")

    if all(results.values()):
        print("\n🎉 Все сервисы подключены успешно!")
        print("   Можно запускать бота: python bot.py")
        sys.exit(0)
    else:
        print("\n⚠️  Некоторые сервисы недоступны.")
        print("   Проверьте настройки в .env файле.")
        sys.exit(1)


if __name__ == '__main__':
    main()
