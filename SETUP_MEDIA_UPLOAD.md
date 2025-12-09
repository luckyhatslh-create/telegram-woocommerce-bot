# Настройка загрузки изображений в WooCommerce

## Проблема

WooCommerce на вашем сервере не может загружать изображения по внешним URL. Это означает, что нужно загружать изображения напрямую через WordPress Media Library API.

## Решение

Для загрузки изображений через WordPress Media API нужно создать **Application Password**.

### Шаг 1: Создание Application Password в WordPress

1. Войдите в админ-панель WordPress: `https://luckyhats.ru/wp-admin`
2. Перейдите в **Пользователи** → **Профиль** (или **Users** → **Profile**)
3. Прокрутите вниз до секции **Application Passwords** (Пароли приложений)
4. В поле "New Application Password Name" введите: `TelegramBot`
5. Нажмите **Add New Application Password**
6. **ВАЖНО:** Скопируйте сгенерированный пароль (он показывается только один раз!)
   - Формат: `xxxx xxxx xxxx xxxx xxxx xxxx`
   - Уберите пробелы: `xxxxxxxxxxxxxxxxxxxxxxxx`

### Шаг 2: Добавление данных в .env

Добавьте следующие строки в файл `.env`:

```bash
# WordPress Authentication для Media Library
WP_USERNAME=ваш_логин_администратора
WP_APP_PASSWORD=скопированный_пароль_без_пробелов
```

Замените:
- `ваш_логин_администратора` - на ваш логин WordPress (обычно это admin или email)
- `скопированный_пароль_без_пробелов` - на пароль приложения без пробелов

### Шаг 3: Тестирование

После добавления данных в `.env`, запустите:

```bash
python3 test_media_upload.py
```

Если всё работает, вы увидите:
```
✅ УСПЕХ! Изображение загружено в Media Library
```

## Альтернативное решение

Если не получается настроить Application Password, можно:

1. **Включить загрузку по URL в WordPress**
   - Добавьте в `wp-config.php`:
   ```php
   define('WP_HTTP_BLOCK_EXTERNAL', false);
   ```

2. **Загружать товары без изображений**
   - Бот создаст товар без фото
   - Изображения можно будет добавить вручную в админке

3. **Использовать внешний хостинг изображений**
   - Например: Cloudinary, ImgBB
   - Загружать изображения туда, а URL использовать в WooCommerce
