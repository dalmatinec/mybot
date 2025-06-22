from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import logging
import json
import os
import re

# Настройка логирования
logger = logging.getLogger(__name__)

router = Router()

# Middleware для проверки бана
from aiogram import BaseMiddleware
from aiogram.types import Message
from database import is_banned

class BanCheckMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message):
            user_id = event.from_user.id
            if is_banned(user_id):
                await event.answer("<b>⛔ Вы заблокированы и не можете использовать бота!</b>", parse_mode="HTML")
                return
        return await handler(event, data)

# Функция для создания меню магазинов с пагинацией
def get_shops_menu(page=1):
    shops_per_page = 10
    try:
        with open('shops.json', 'r', encoding='utf-8') as f:
            shops = json.load(f)
    except FileNotFoundError:
        logger.error("shops.json not found")
        shops = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in shops.json")
        shops = []

    start = (page - 1) * shops_per_page
    end = start + shops_per_page
    page_shops = shops[start:end]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if not page_shops:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="📋 Магазины не найдены", callback_data="main_menu")])
    else:
        for i in range(0, len(page_shops), 2):
            row = [
                InlineKeyboardButton(text=f"▫️ {page_shops[i]['name']} ", callback_data=f"shop_{page_shops[i]['order']}")
            ]
            if i + 1 < len(page_shops):
                row.append(InlineKeyboardButton(text=f"▫️ {page_shops[i + 1]['name']} ", callback_data=f"shop_{page_shops[i + 1]['order']}"))
            keyboard.inline_keyboard.append(row)
    
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"shops_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu"))
    if end < len(shops):
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"shops_page_{page + 1}"))
    keyboard.inline_keyboard.append(nav_row)
    
    return keyboard

# Функция для создания меню рекомендаций
def get_recommendations_menu():
    try:
        with open('shops.json', 'r', encoding='utf-8') as f:
            shops = [s for s in json.load(f) if s.get("is_top", False)]
            shops = sorted(shops, key=lambda x: x.get("order", float('inf')))[:5]
    except FileNotFoundError:
        logger.error("shops.json not found")
        shops = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in shops.json")
        shops = []

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for shop in shops:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"✨ {shop['name']} ", callback_data=f"recommendation_{shop['name']}")
        ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    ])
    return keyboard

# Функция для создания меню вакансий с пагинацией
def get_jobs_menu(page=1):
    jobs_per_page = 10
    try:
        with open('jobs.json', 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except FileNotFoundError:
        logger.error("jobs.json not found")
        jobs = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in jobs.json")
        jobs = []

    start = (page - 1) * jobs_per_page
    end = start + jobs_per_page
    page_jobs = jobs[start:end]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if not page_jobs:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="📋 Вакансий не найдено", callback_data="main_menu")])
    else:
        for i in range(0, len(page_jobs), 2):
            row = [
                InlineKeyboardButton(text=f"🧑‍💼 {page_jobs[i]['name']} ", callback_data=f"job_{page_jobs[i]['name']}")
            ]
            if i + 1 < len(page_jobs):
                row.append(InlineKeyboardButton(text=f"🧑‍💼 {page_jobs[i + 1]['name']} ", callback_data=f"job_{page_jobs[i + 1]['name']}"))
            keyboard.inline_keyboard.append(row)
    
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"work_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu"))
    if end < len(jobs):
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"work_page_{page + 1}"))
    keyboard.inline_keyboard.append(nav_row)
    
    return keyboard

# Обработка кнопки "Выбрать магазины"
@router.callback_query(F.data == "shops")
async def show_shops(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Условные обозначения: 🏴‍☠</b>\n\n"
        "<b>🌳 - Сорт</b>\n"
        "<b>🌲 - Дус | Сд</b>\n"
        "<b>🌑 - Гаш | Руч</b>\n"
        "<b>🍂 - Первак | Центр</b>\n"
        "<b>🍃 - Шала | Трим</b>\n"
        "<b>🍯 - Вакс</b>\n"
        "<b>🍄 - Грибы</b>\n"
        "<b>🍫 - КаннаФуд</b>\n\n"
        "<b>Выберите магазин:🕹</b>",
        reply_markup=get_shops_menu(),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} opened shops menu")
    await callback.answer()

# Обработка пагинации магазинов
@router.callback_query(F.data.startswith("shops_page_"))
async def change_shops_page(callback: CallbackQuery):
    page = int(callback.data.replace("shops_page_", ""))
    await callback.message.delete()
    await callback.message.answer(
        "<b>🗂 Выберите магазин 🌿</b>",
        reply_markup=get_shops_menu(page),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} changed shops page to {page}")
    await callback.answer()

# Обработка выбора магазина
@router.callback_query(F.data.startswith("shop_"))
async def select_shop(callback: CallbackQuery):
    from database import add_shop_click
    order = int(callback.data.replace("shop_", ""))
    try:
        with open('shops.json', 'r', encoding='utf-8') as f:
            shops = json.load(f)
            shop = next((s for s in shops if s["order"] == order), None)
    except FileNotFoundError:
        logger.error("shops.json not found")
        shop = None
    except json.JSONDecodeError:
        logger.error("Invalid JSON in shops.json")
        shop = None
    
    if not shop:
        await callback.message.delete()
        await callback.message.answer(
            "<b>❌ Магазин не найден!</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="shops")]
            ]),
            parse_mode="HTML"
        )
        logger.error(f"Shop with order {order} not found for user {callback.from_user.id}")
        await callback.answer()
        return
    
    add_shop_click(callback.from_user.id, shop['name'])
    
    assortment_text = ""
    if shop["assortment"]:
        for item in shop["assortment"]:
            # Разделяем на название и цены, используя регулярное выражение для поиска чисел
            match = re.match(r'^(.*?)(?:\s(\d+\.?\d*\w+.*))?$', item["item"].strip())
            if match:
                name = match.group(1).strip() or "Сорт"  # Полное название сорта
                price_part = match.group(2)  # Цены
                if price_part:
                    assortment_text += f"<b>{name}</b>\n💲 {price_part}\n\n"
                else:
                    assortment_text += f"<b>{name}</b>\n\n"
        assortment_text = assortment_text.rstrip("\n")  # Убираем лишний отступ в конце
    else:
        assortment_text = "Нет ассортимента"
    
    extra_text = f"\n{shop['extra_text']} 🛵" if shop["extra_text"] else ""
    message_text = (
        f"<b>🏬 Магазин: <b>{shop['name']}</b></b>\n\n"
        f"<b>📋 Ассортимент: 🌿</b>\n\n"
        f"{assortment_text}"
        f"{extra_text}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if shop.get("contacts") and shop["contacts"] and shop["contacts"][0]:  # Проверяем, есть ли хотя бы один валидный контакт
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🛒 Купить 📲", url=f"https://t.me/{shop['contacts'][0]}")])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="shops")
    ])
    
    await callback.message.delete()
    if shop.get("image") and shop["image"] and os.path.exists(f"media/{shop['image']}"):
        with open(f"media/{shop['image']}", "rb") as photo:
            await callback.message.answer_photo(
                photo=photo,
                caption=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    else:
        await callback.message.answer(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    logger.info(f"User {callback.from_user.id} selected shop: {shop['name']}")
    await callback.answer()

# Обработка кнопки "Рекомендации"
@router.callback_query(F.data == "recommendations")
async def show_recommendations(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Рекомендации ✨</b>\n\n"
        "<b>Магазины с высоким уровнем доверия, сервиса и качества 💯 %</b>\n\n"
        "<b>Выберите и нажмите кнопку:⬇️</b>",
        reply_markup=get_recommendations_menu(),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} opened recommendations")
    await callback.answer()

# Обработка выбора рекомендованного магазина
@router.callback_query(F.data.startswith("recommendation_"))
async def select_recommendation(callback: CallbackQuery):
    from database import add_shop_click
    shop_name = callback.data.replace("recommendation_", "")
    try:
        with open('shops.json', 'r', encoding='utf-8') as f:
            shops = json.load(f)
            shop = next((s for s in shops if s["name"] == shop_name), None)
    except FileNotFoundError:
        logger.error("shops.json not found")
        shop = None
    except json.JSONDecodeError:
        logger.error("Invalid JSON in shops.json")
        shop = None
    
    if not shop:
        await callback.message.delete()
        await callback.message.answer(
            "<b>❌ Магазин не найден!</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="recommendations")]
            ]),
            parse_mode="HTML"
        )
        logger.error(f"Recommendation {shop_name} not found for user {callback.from_user.id}")
        await callback.answer()
        return
    
    add_shop_click(callback.from_user.id, shop_name)
    
    assortment_text = ""
    if shop["assortment"]:
        for item in shop["assortment"]:
            # Разделяем на название и цены, используя регулярное выражение для поиска чисел
            match = re.match(r'^(.*?)(?:\s(\d+\.?\d*\w+.*))?$', item["item"].strip())
            if match:
                name = match.group(1).strip() or "Сорт"  # Полное название сорта
                price_part = match.group(2)  # Цены
                if price_part:
                    assortment_text += f"<b>{name}</b>\n💲 {price_part}\n\n"
                else:
                    assortment_text += f"<b>{name}</b>\n\n"
        assortment_text = assortment_text.rstrip("\n")  # Убираем лишний отступ в конце
    else:
        assortment_text = "Нет ассортимента"
    
    extra_text = f"\n{shop['extra_text']} 🛵" if shop["extra_text"] else ""
    message_text = (
        f"<b>🏬 Магазин: <b>{shop_name}</b></b>\n\n"
        f"<b>📋 Ассортимент: 🌿</b>\n\n"
        f"{assortment_text}"
        f"{extra_text}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if shop.get("contacts") and shop["contacts"] and shop["contacts"][0]:  # Проверяем, есть ли хотя бы один валидный контакт
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🛒 Купить 📲", url=f"https://t.me/{shop['contacts'][0]}")])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="recommendations")
    ])
    
    await callback.message.delete()
    if shop.get("image") and shop["image"] and os.path.exists(f"media/{shop['image']}"):
        with open(f"media/{shop['image']}", "rb") as photo:
            await callback.message.answer_photo(
                photo=photo,
                caption=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    elif os.path.exists("media/topshop_default.jpg"):
        with open("media/topshop_default.jpg", "rb") as photo:
            await callback.message.answer_photo(
                photo=photo,
                caption=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    else:
        await callback.message.answer(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    logger.info(f"User {callback.from_user.id} selected recommendation: {shop_name}")
    await callback.answer()

# Обработка кнопки "Работа"
@router.callback_query(F.data == "work")
async def show_work(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "<b>Работа 💼</b>\n\n"
        "<b>▫️ Актуальные вакансии</b>\n"
        "<b>▫️ Работа строго в органик проектах. ( напишите жалобу если вам предлагают иной вариант )</b>\n\n"
        "<b>Выберите и нажмите кнопку с именем нашего партнёра что бы открыть полную информацию о работе 📣</b>",
        reply_markup=get_jobs_menu(),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} opened work section")
    await callback.answer()

# Обработка пагинации вакансий
@router.callback_query(F.data.startswith("work_page_"))
async def change_work_page(callback: CallbackQuery):
    page = int(callback.data.replace("work_page_", ""))
    await callback.message.delete()
    await callback.message.answer(
        "<b>💼 Работа 🌱</b>",
        reply_markup=get_jobs_menu(page),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} changed work page to {page}")
    await callback.answer()

# Обработка выбора вакансии
@router.callback_query(F.data.startswith("job_"))
async def select_job(callback: CallbackQuery):
    job_name = callback.data.replace("job_", "")
    try:
        with open('jobs.json', 'r', encoding='utf-8') as f:
            jobs = json.load(f)
            job = next((j for j in jobs if j["name"] == job_name), None)
    except FileNotFoundError:
        logger.error("jobs.json not found")
        job = None
    except json.JSONDecodeError:
        logger.error("Invalid JSON in jobs.json")
        job = None

    if not job:
        await callback.message.delete()
        await callback.message.answer(
            "<b>❌ Вакансия не найдена!</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="work")]
            ]),
            parse_mode="HTML"
        )
        logger.error(f"Job {job_name} not found for user {callback.from_user.id}")
        await callback.answer()
        return

    vacancy_text = job.get("vacancy", "Нет описания")
    salary_text = job.get("salary", "Не указана")
    conditions_text = job.get("conditions", "Не указаны")
    message_text = (
        f"<b>#JobsHunter</b>\n\n"
        f"💈 Партнёр: {job_name}\n"
        f"➖➖➖➖➖\n"
        f"💼 Вакансия: {vacancy_text}\n"
        f"➖➖➖➖➖\n"
        f"💰 Оплата труда: {salary_text}\n"
        f"➖➖➖➖➖\n"
        f"🔅 Детали: {conditions_text}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if job.get("contacts") and job["contacts"] and job["contacts"][0]:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Связаться 📲", url=f"https://t.me/{job['contacts'][0]}")])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="work")
    ])

    await callback.message.delete()
    await callback.message.answer(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} selected job: {job_name}")
    await callback.answer()

def register_handlers(dp):
    dp.include_router(router)