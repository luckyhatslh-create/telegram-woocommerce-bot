#!/bin/bash
# Скрипт запуска Telegram бота с очищенными переменными окружения

# Очищаем переменные окружения, которые могут конфликтовать с .env
unset ANTHROPIC_MODEL
unset WC_KEY
unset WC_SECRET

# Запускаем бота
python3 bot.py
