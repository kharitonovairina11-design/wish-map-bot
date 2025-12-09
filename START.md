# Инструкция по запуску Wish Map Bot

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка .env

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=your_telegram_bot_token
KOLORS_API_KEY=your_kolors_api_key
BACKEND_URL=http://localhost:8000
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 3. Запуск Backend

```bash
cd app/api
python main.py
```

Или:

```bash
cd app/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Запуск Bot

В отдельном терминале:

```bash
cd app/bot
python bot.py
```

## Проверка работы

1. Откройте Telegram и найдите вашего бота
2. Отправьте `/start`
3. Отправьте селфи
4. Выберите формат
5. Введите 3-9 желаний
6. Напишите `ГОТОВО`

## Устранение проблем

### Ошибка 503

1. Проверьте, что backend запущен на порту 8000
2. Проверьте логи backend для деталей ошибки
3. Убедитесь, что `KOLORS_API_KEY` установлен в `.env`
4. Проверьте баланс API ключа Kolors

### Ошибки импорта

Убедитесь, что вы запускаете из правильной директории:
- Backend: `cd app/api && python main.py`
- Bot: `cd app/bot && python bot.py`

### Проблемы с Kolors API

Проверьте логи backend - там будет детальная информация о запросах к Kolors API.

