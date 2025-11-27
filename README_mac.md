# ContentFlow AI — Telegram-бот (macOS)

## Запуск на macOS
```bash
cd contentflow_ai_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
open -a TextEdit .env   # вставьте ваши ключи
python main.py
```
Если увидите `Bot is running…` — всё работает. Откройте бота в Telegram и отправьте /start.

## Файлы
- main.py — код бота
- requirements.txt — зависимости
- .env.example — шаблон ключей
- data/users.json — файл сохранения лимитов

## Частые ошибки
- Нет ответа бота — проверьте, что терминал с `python main.py` открыт и ключи верные.
- ModuleNotFoundError — активируйте venv (`source venv/bin/activate`) и установите зависимости.
