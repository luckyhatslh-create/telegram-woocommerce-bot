#!/usr/bin/env python3
"""
Скрипт для проверки подключения к API сервисам
"""
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
        response = requests.get(f'https://api.telegram.org/bot{token}/getMe')
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Telegram Bot подключен: @{bot_info['result']['username']}")
            return True
        else:
            print(f"❌ Ошибка подключения к Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def check_openai():
    """Проверка OpenAI API Key"""
    print("\n🔍 Проверка OpenAI API...")
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY не установлен в .env")
        return False
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        # Пробуем простой запрос
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        print("✅ OpenAI API подключен")
        print(f"   Модель: {response.model}")
        
        # Проверяем доступ к моделям
        print("\n📋 Проверка доступа к моделям:")
        models_to_check = ["gpt-4o", "dall-e-3"]
        
        for model in models_to_check:
            try:
                if model.startswith("gpt"):
                    client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    print(f"   ✅ {model} - доступен")
            except Exception as e:
                if "model" in str(e).lower():
                    print(f"   ❌ {model} - недоступен")
                else:
                    print(f"   ✅ {model} - доступен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def check_woocommerce():
    """Проверка WooCommerce API"""
    print("\n🔍 Проверка WooCommerce API...")
    
    url = os.getenv('WC_URL')
    key = os.getenv('WC_KEY')
    secret = os.getenv('WC_SECRET')
    
    if not all([url, key, secret]):
        print("❌ WooCommerce credentials не установлены в .env")
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
        
        # Пробуем получить информацию о магазине
        response = wcapi.get("system_status")
        
        if response.status_code == 200:
            print(f"✅ WooCommerce API подключен")
            print(f"   URL: {url}")
            
            # Пробуем получить продукты
            products = wcapi.get("products", params={"per_page": 1})
            if products.status_code == 200:
                print(f"   ✅ Доступ к продуктам работает")
            
            return True
        else:
            print(f"❌ Ошибка подключения: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    """Главная функция"""
    print("=" * 60)
    print("🔧 ПРОВЕРКА ПОДКЛЮЧЕНИЯ К API СЕРВИСАМ")
    print("=" * 60)
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("\n❌ Файл .env не найден!")
        print("   Создайте его на основе .env.example:")
        print("   cp .env.example .env")
        sys.exit(1)
    
    results = {
        'Telegram': check_telegram(),
        'OpenAI': check_openai(),
        'WooCommerce': check_woocommerce()
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
