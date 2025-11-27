import os
import asyncio
import json
import base64
from pathlib import Path

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    BufferedInputFile,
)
from dotenv import load_dotenv
from openai import OpenAI

# ===== ЗАГРУЗКА КЛЮЧЕЙ =====

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в .env")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не найден в .env")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== ХРАНИЛИЩЕ ПОЛЬЗОВАТЕЛЕЙ (ТОЛЬКО СОСТОЯНИЕ, БЕЗ ЛИМИТОВ) =====

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"

def load_users() -> dict:
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_users(data: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users: dict = load_users()

def get_user(uid: int) -> dict:
    uid = str(uid)
    if uid not in users:
        users[uid] = {
            "mode": None,           # режим ожидания (post_wait_topic, desc_wait_topic, image_*)
            "image_purpose": None,  # для каких целей картинка
        }
        save_users(users)
    return users[uid]

def update_user(uid: int, **kwargs):
    uid = str(uid)
    u = get_user(uid)
    u.update(kwargs)
    users[uid] = u
    save_users(users)

# ===== КЛАВИАТУРЫ =====

kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Сгенерировать пост")],
        [KeyboardButton(text="🛍 Описание товара")],
        [KeyboardButton(text="💡 Идеи для контента")],
        [KeyboardButton(text="🎨 Сгенерировать изображение")],
    ],
    resize_keyboard=True,
)

kb_image_type = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📸 Пост для Instagram")],
        [KeyboardButton(text="📱 Сторис")],
        [KeyboardButton(text="🥗 Фото еды / блюд")],
        [KeyboardButton(text="📦 Фото товаров")],
        [KeyboardButton(text="🎨 Фон / баннер")],
        [KeyboardButton(text="🧾 Обложка меню")],
        [KeyboardButton(text="🔹 Логотип / иконка")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
)

# ===== ГЕНЕРАЦИЯ ТЕКСТА =====

async def generate_ai_text(topic: str, mode: str) -> str:
    if mode == "post":
        system = "Ты опытный русскоязычный SMM-копирайтер."
        user = (
            f"Напиши 1 пост для Instagram по теме: {topic}. "
            "Объем 700–900 знаков, живой разговорный стиль, добавь эмодзи и призыв к действию."
        )
    elif mode == "desc":
        system = "Ты специалист по маркетплейсам (Wildberries, Ozon)."
        user = (
            "Сделай SEO-описание карточки товара для маркетплейса по характеристикам: "
            f"{topic}. Объем 600–800 знаков, сделай заголовок, список преимуществ и 8–10 хэштегов."
        )
    elif mode == "ideas":
        system = "Ты креативный контент-маркетолог."
        user = (
            f"Сгенерируй 10 идей контента для ниши: {topic}. "
            "Для каждой идеи укажи формат (пост, сторис, рилс), тему и краткий тезис."
        )
    else:
        system = "Ты полезный ассистент."
        user = f"Сделай короткий полезный текст по теме: {topic}."

    def _call():
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content.strip()

    return await asyncio.to_thread(_call)

# ===== ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЯ =====

async def generate_image(message: types.Message, user_prompt: str) -> None:
    u = get_user(message.from_user.id)
    purpose = u.get("image_purpose") or "общее назначение"

    await message.answer("🎨 Генерирую изображение… Это может занять несколько секунд.")

    def _call():
        prompt = (
            f"Фотореалистичное изображение. Назначение: {purpose}. "
            f"Техническое задание: {user_prompt}. "
            "Стиль: реалистичная фотография, мягкий свет, высокий уровень детализации."
        )
        resp = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
        )
        b64 = resp.data[0].b64_json
        return base64.b64decode(b64)

    try:
        img_bytes = await asyncio.to_thread(_call)
        file = BufferedInputFile(img_bytes, filename="image.png")
        await message.answer_photo(
            file,
            caption="✅ Изображение готово.",
        )
        update_user(message.from_user.id, mode=None, image_purpose=None)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка генерации изображения: {e}")
        update_user(message.from_user.id, mode=None, image_purpose=None)

# ===== ОБЩИЕ ХЭНДЛЕРЫ =====

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    get_user(message.from_user.id)  # чтобы пользователь создался
    await message.answer(
        "👋 Привет! Я контент-бот (тестовый режим, генерации без ограничений).\n\n"
        "Я могу:\n"
        "• писать посты для соцсетей\n"
        "• делать описания товаров\n"
        "• придумывать идеи\n"
        "• генерировать фотореалистичные изображения\n\n"
        "Выбери действие на клавиатуре 👇",
        reply_markup=kb_main,
    )

# ----- Кнопки текста -----

@dp.message(F.text == "📝 Сгенерировать пост")
async def ask_post_topic(message: types.Message):
    update_user(message.from_user.id, mode="post_wait_topic")
    await message.answer("✍️ Напиши тему поста.", reply_markup=kb_main)

@dp.message(F.text == "🛍 Описание товара")
async def ask_desc_topic(message: types.Message):
    update_user(message.from_user.id, mode="desc_wait_topic")
    await message.answer("📦 Опиши товар: категория, материал, цвет, размер, особенности.", reply_markup=kb_main)

@dp.message(F.text == "💡 Идеи для контента")
async def ask_ideas_topic(message: types.Message):
    update_user(message.from_user.id, mode="ideas_wait_topic")
    await message.answer("Для какой ниши нужны идеи?\nНапример: «ПП-меню на неделю в Орле».", reply_markup=kb_main)

# ----- Кнопка генерации изображения -----

@dp.message(F.text == "🎨 Сгенерировать изображение")
async def on_image_main(message: types.Message):
    update_user(message.from_user.id, mode="image_choose_type", image_purpose=None)
    await message.answer(
        "Для каких целей нужно изображение?\nВыбери вариант:",
        reply_markup=kb_image_type,
    )

# ===== МАППИНГ ЦЕЛЕЙ ДЛЯ КАРТИНОК =====

def map_image_purpose(btn_text: str) -> str | None:
    mapping = {
        "📸 Пост для Instagram": "пост для Instagram",
        "📱 Сторис": "сторис в Instagram/Telegram",
        "🥗 Фото еды / блюд": "фото блюда / еды для ПП-проекта",
        "📦 Фото товаров": "фото товара для маркетплейса или каталога",
        "🎨 Фон / баннер": "дизайнерский фон / баннер",
        "🧾 Обложка меню": "обложка меню сервиса питания",
        "🔹 Логотип / иконка": "логотип или иконка бренда",
    }
    return mapping.get(btn_text)

# ===== ГЛАВНЫЙ ХЭНДЛЕР ТЕКСТА (СОСТОЯНИЯ) =====

@dp.message()
async def on_text(message: types.Message):
    u = get_user(message.from_user.id)
    mode = u.get("mode")

    # Выбор типа изображения
    if mode == "image_choose_type":
        if message.text == "⬅️ Назад":
            update_user(message.from_user.id, mode=None, image_purpose=None)
            await message.answer("Ок, возвращаюсь в главное меню.", reply_markup=kb_main)
            return

        purpose = map_image_purpose(message.text)
        if purpose is None:
            await message.answer("Пожалуйста, выбери один из вариантов на клавиатуре 👇", reply_markup=kb_image_type)
            return

        update_user(message.from_user.id, mode="image_wait_prompt", image_purpose=purpose)
        await message.answer(
            f"Отлично, делаем изображение под цель: {purpose}.\n\n"
            "Теперь опиши, что должно быть на изображении (ТЗ):\n"
            "• что на картинке\n"
            "• ракурс (крупный план / сверху)\n"
            "• фон (однотонный / кухня / зал)\n"
            "• есть ли люди и т.д.",
            reply_markup=kb_main,
        )
        return

    # Ожидаем ТЗ для картинки
    if mode == "image_wait_prompt":
        prompt = message.text.strip()
        if not prompt:
            await message.answer("Опиши, пожалуйста, что должно быть на изображении.")
            return
        await generate_image(message, prompt)
        return

    # Ожидаем тему поста
    if mode == "post_wait_topic":
        topic = message.text.strip()
        update_user(message.from_user.id, mode=None)
        if not topic:
            await message.answer("Напиши тему поста текстом.")
            return
        await message.answer("⏳ Генерирую пост…")
        try:
            text = await generate_ai_text(topic, mode="post")
            await message.answer(f"📝 Готовый пост:\n\n{text}", reply_markup=kb_main)
        except Exception as e:
            await message.answer(f"⚠️ Ошибка генерации: {e}", reply_markup=kb_main)
        return

    # Ожидаем характеристики товара
    if mode == "desc_wait_topic":
        topic = message.text.strip()
        update_user(message.from_user.id, mode=None)
        if not topic:
            await message.answer("Опиши товар текстом.")
            return
        await message.answer("⏳ Делаю описание товара…")
        try:
            text = await generate_ai_text(topic, mode="desc")
            await message.answer(f"📦 Описание товара:\n\n{text}", reply_markup=kb_main)
        except Exception as e:
            await message.answer(f"⚠️ Ошибка генерации: {e}", reply_markup=kb_main)
        return

    # Ожидаем нишу для идей
    if mode == "ideas_wait_topic":
        topic = message.text.strip()
        update_user(message.from_user.id, mode=None)
        if not topic:
            await message.answer("Напиши, для какой ниши нужны идеи.")
            return
        await message.answer("💡 Генерирую идеи…")
        try:
            text = await generate_ai_text(topic, mode="ideas")
            await message.answer(f"💡 Идеи для контента:\n\n{text}", reply_markup=kb_main)
        except Exception as e:
            await message.answer(f"⚠️ Ошибка генерации: {e}", reply_markup=kb_main)
        return

    # Если никакого режима нет
    await message.answer(
        "Я пока понимаю только эти действия:\n"
        "• 📝 Сгенерировать пост\n"
        "• 🛍 Описание товара\n"
        "• 💡 Идеи для контента\n"
        "• 🎨 Сгенерировать изображение\n\n"
        "Выбери пункт на клавиатуре 👇",
        reply_markup=kb_main,
    )

# ===== ЗАПУСК =====

async def main():
    print("Content bot (UNLIMITED mode) is running…")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
