# ContentFlow AI — Telegram-бот (начальный уровень)

## Шаги запуска
1) Создайте бота в @BotFather → /newbot → получите BOT_TOKEN.
2) Создайте ключ на platform.openai.com → OPENAI_API_KEY.
3) Установите Python 3.10+.
4) Откройте терминал в папке проекта и выполните:
```
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate
pip install -r requirements.txt
```
5) Создайте файл `.env` (скопируйте из `.env.example`) и вставьте ваши ключи.
6) Запустите:
```
python main.py
```

## Использование
- Нажмите «📝 Сгенерировать пост» — отправьте тему.
- «🛍 Описание товара» — отправьте характеристики.
- «💡 Идеи для контента» — отправьте нишу.

Дано 5 бесплатных генераций на пользователя. Лимиты хранятся в `data/users.json`.

## Деплой
- Railway / Render: добавьте переменные окружения `BOT_TOKEN`, `OPENAI_API_KEY`, задеплойте репозиторий.
