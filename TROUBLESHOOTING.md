# Устранение неполадок

## Проблема: "Object of type bytes is not JSON serializable"

**Симптомы:** Бот запускается, но при отправке фото выдает ошибку.

**Причина:** В `providers/anthropic.py` передавались сырые байты вместо base64-encoded строки.

**Решение:** Обновите до последней версии - исправление добавлено в commit `d0579fb`.

## Проблема: "num_inference_steps: Must be less than or equal to 4"

**Симптомы:** Anthropic работает, но Replicate выдает ошибку валидации.

**Причина:** Модель `flux-schnell` поддерживает максимум 4 шага inference, а в `.env` было `STEPS_PREVIEW=20`.

**Решение:**
1. Обновите `.env`:
   ```bash
   STEPS_PREVIEW=4
   STEPS_HQ=4
   ```
2. Или используйте модель `flux-dev` если нужно больше шагов (платная).

## Проблема: Бот использует старую модель Anthropic

**Симптомы:** В `.env` указана правильная модель, но используется старая.

**Причина:** В оболочке (shell) экспортирована переменная `ANTHROPIC_MODEL`, которая переопределяет `.env`.

**Решение:**
1. Используйте скрипт `start_bot.sh` для запуска:
   ```bash
   ./start_bot.sh
   ```
2. Или вручную очистите переменные:
   ```bash
   unset ANTHROPIC_MODEL WC_KEY WC_SECRET
   python3 bot.py
   ```

## Проблема: "TELEGRAM_BOT_TOKEN не задан"

**Причина:** `load_dotenv()` вызывается после импорта `config`.

**Решение:** Обновите до последней версии - порядок импортов исправлен в `bot.py`.

## Проблема: "This event loop is already running" (Python 3.13)

**Причина:** Конфликт event loops в Python 3.13.

**Решение:** Обновите до последней версии - используется синхронный `main()` в commit `ac32316`.

## Рекомендации

1. **Всегда используйте виртуальное окружение:**
   ```bash
   source .venv/bin/activate
   ```

2. **Перед запуском проверьте API:**
   ```bash
   python3 check_api.py
   ```

3. **Запускайте бота через скрипт:**
   ```bash
   ./start_bot.sh
   ```

4. **Для отладки включите подробное логирование:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Доступные модели Anthropic

В зависимости от вашего API tier, доступны разные модели:

- `claude-3-haiku-20240307` - быстрая, дешевая (работает у вас)
- `claude-3-sonnet-20240229` - баланс скорости и качества
- `claude-3-opus-20240229` - лучшее качество, медленнее
- `claude-3-5-sonnet-20241022` - новая версия (может быть недоступна)

## Модели FLUX на Replicate

- `black-forest-labs/flux-schnell` - быстрая, max 4 steps
- `black-forest-labs/flux-dev` - больше настроек, платная
- `black-forest-labs/flux-fill-pro` - для inpainting
