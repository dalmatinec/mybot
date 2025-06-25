from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import logging
import json
import os
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
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
    shops_per_page = 14
    try:
        with open('shops.json', 'r', encoding='utf-8') as f:
            shops = json.load(f)
            logger.info(f"Successfully loaded {len(shops)} shops from shops.json")
    except FileNotFoundError:
        logger.error("shops.json not found. Check if the file exists in the bot's directory.")
        shops = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in shops.json. Please ensure the file is valid JSON.")
        shops = []
    except Exception as e:
        logger.error(f"Unexpected error loading shops.json: {str(e)}")
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

    logger.info(f"Generated shops menu with {len(keyboard.inline_keyboard)} rows")
    return keyboard

# Функция для создания меню рекомендаций
def get_recommendations_menu():
    try:
        with open('shops.json', 'r', encoding='utf-8') as f:
            shops = [s for s in json.load(f) if s.get("is_top", False)]
            shops = sorted(shops, key=lambda x: x.get("order", float('inf')))[:5]
            logger.info(f"Loaded {len(shops)} recommendations from shops.json")
    except FileNotFoundError:
        logger.error("shops.json not found. Check if the file exists in the bot's directory.")
        shops = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in shops.json. Please ensure the file is valid JSON.")
        shops = []
    except Exception as e:
        logger.error(f"Unexpected error loading shops.json for recommendations: {str(e)}")
        shops = []

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if not shops:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="📋 Рекомендаций не найдено", callback_data="main_menu")])
    else:
        for shop in shops:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"✨ {shop['name']} ", callback_data=f"recommendation_{shop['name']}")
            ])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")
    ])

    logger.info(f"Generated recommendations menu with {len(keyboard.inline_keyboard)} rows")
    return keyboard

# Функция для создания меню вакансий с пагинацией
def get_jobs_menu(page=1):
    jobs_per_page = 10
    try:
        with open('jobs.json', 'r', encoding='utf-8') as f:
            jobs = json.load(f)
            logger.info(f"Successfully loaded {len(jobs)} jobs from jobs.json")
    except FileNotFoundError:
        logger.error("jobs.json not found. Check if the file exists in the bot's directory.")
        jobs = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in jobs.json. Please ensure the file is valid JSON.")
        jobs = []
    except Exception as e:
        logger.error(f"Unexpected error loading jobs.json: {str(e)}")
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

    logger.info(f"Generated jobs menu with {len(keyboard.inline_keyboard)} rows")
    return keyboard

# Функция для создания меню городов с пагинацией
def get_cities_menu(page=1):
    cities_per_page = 10
    try:
        with open('city.json', 'r', encoding='utf-8') as f:
            cities = json.load(f)
            logger.info(f"Successfully loaded {len(cities)} cities from city.json: {cities}")
    except FileNotFoundError:
        logger.error("city.json not found. Check if the file exists in the bot's directory.")
        cities = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in city.json. Please ensure the file is valid JSON.")
        cities = []
    except Exception as e:
        logger.error(f"Unexpected error loading city.json: {str(e)}")
        cities = []

    start = (page - 1) * cities_per_page
    end = start + cities_per_page
    page_cities = cities[start:end]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if not page_cities:
        logger.warning("No cities found to display in menu")
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="📋 Города не найдены", callback_data="main_menu")])
    else:
        for i in range(0, len(page_cities), 2):
            row = [
                InlineKeyboardButton(text=f"{page_cities[i]['name']} ", callback_data=f"city_{page_cities[i]['order']}")
            ]
            if i + 1 < len(page_cities):
                row.append(InlineKeyboardButton(text=f"{page_cities[i + 1]['name']} ", callback_data=f"city_{page_cities[i + 1]['order']}"))
            keyboard.inline_keyboard.append(row)

    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"cities_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu"))
    if end < len(cities):
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"cities_page_{page + 1}"))
    keyboard.inline_keyboard.append(nav_row)

    logger.info(f"Generated cities menu with {len(keyboard.inline_keyboard)} rows")
    return keyboard

# Функция для создания меню магазинов города
def get_city_shops_menu(city_order, page=1):
    shops_per_page = 14
    try:
        with open('city_shops.json', 'r', encoding='utf-8') as f:
            shops = [s for s in json.load(f) if s.get("city_order") == city_order]
            logger.info(f"Loaded {len(shops)} shops for city_order {city_order} from city_shops.json")
    except FileNotFoundError:
        logger.error("city_shops.json not found. Check if the file exists in the bot's directory.")
        shops = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in city_shops.json. Please ensure the file is valid JSON.")
        shops = []
    except Exception as e:
        logger.error(f"Unexpected error loading city_shops.json: {str(e)}")
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
                InlineKeyboardButton(text=f"▫️ {page_shops[i]['name']} ", callback_data=f"shop_{page_shops[i]['order']}_{city_order}")
            ]
            if i + 1 < len(page_shops):
                row.append(InlineKeyboardButton(text=f"▫️ {page_shops[i + 1]['name']} ", callback_data=f"shop_{page_shops[i + 1]['order']}_{city_order}"))
            keyboard.inline_keyboard.append(row)

    # Проверка на необходимость пагинации
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(text="⬅ Назад", callback_data=f"shops_page_{city_order}_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text="🔙 Назад к городам", callback_data="cities_countries"))
    if end < len(shops):
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡", callback_data=f"shops_page_{city_order}_{page + 1}"))
    if nav_row:
        keyboard.inline_keyboard.append(nav_row)

    logger.info(f"Generated city shops menu with {len(keyboard.inline_keyboard)} rows")
    return keyboard

# Обработка кнопки "Выбрать магазины"
@router.callback_query(F.data == "shops")
async def show_shops(callback: CallbackQuery):
    logger.info(f"Processing 'shops' callback for user {callback.from_user.id}")
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
    logger.info(f"Sent shops menu for user {callback.from_user.id}")
    await callback.answer()

# Обработка пагинации магазинов
@router.callback_query(F.data.startswith("shops_page_"))
async def change_shops_page(callback: CallbackQuery):
    page = int(callback.data.replace("shops_page_", ""))
    await callback.message.delete()
    await callback.message.answer(
        "<b>🗂 Выберите магазин 🕹</b>",
        reply_markup=get_shops_menu(page),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} changed shops page to {page}")
    await callback.answer()

# Обработка выбора магазина
@router.callback_query(F.data.startswith("shop_"))
async def select_shop(callback: CallbackQuery):
    from database import add_shop_click
    parts = callback.data.replace("shop_", "").split("_")
    order = int(parts[0])
    city_order = int(parts[1]) if len(parts) > 1 else None
    try:
        with open('shops.json' if not city_order else 'city_shops.json', 'r', encoding='utf-8') as f:
            shops = json.load(f)
            shop = next((s for s in shops if s["order"] == order), None)
    except FileNotFoundError:
        logger.error(f"{'shops.json' if not city_order else 'city_shops.json'} not found")
        shop = None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {'shops.json' if not city_order else 'city_shops.json'}")
        shop = None

    if not shop:
        await callback.message.delete()
        await callback.message.answer(
            "<b>❌ Магазин не найден!</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="shops" if not city_order else f"city_{city_order}")]
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
            match = re.match(r'^(.*?)(?:\s(\d+\.?\d*\w+.*))?$', item["item"].strip())
            if match:
                name = match.group(1).strip() or "Сорт"
                price_part = match.group(2)
                if price_part:
                    assortment_text += f"<b>{name}</b>\n💲 {price_part}\n\n"
                else:
                    assortment_text += f"<b>{name}</b>\n\n"
        assortment_text = assortment_text.rstrip("\n")
    else:
        assortment_text = "Нет ассортимента"

    extra_text = f"\n{shop['extra_text']} 🛵" if shop.get("extra_text") else ""
    message_text = (
        f"<b>🏬 Магазин: <b>{shop['name']}</b></b>\n\n"
        f"<b>📋 Ассортимент: 🛍</b>\n\n"
        f"{assortment_text}\n"
        f"➖➖➖➖➖\n"
        f"{extra_text}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if shop.get("contacts") and shop["contacts"] and shop["contacts"][0]:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="🛒 Купить 📲", url=f"https://t.me/{shop['contacts'][0]}")])
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="shops" if not city_order else f"city_{city_order}")
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
    logger.info(f"Processing 'recommendations' callback for user {callback.from_user.id}")
    await callback.message.delete()
    await callback.message.answer(
        "<b>Рекомендации ✨</b>\n\n"
        "<b>Магазины с высоким уровнем доверия, сервиса и качества 💯 %</b>\n\n"
        "<b>Выберите и нажмите кнопку:⬇️</b>",
        reply_markup=get_recommendations_menu(),
        parse_mode="HTML"
    )
    logger.info(f"Sent recommendations menu for user {callback.from_user.id}")
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
            match = re.match(r'^(.*?)(?:\s(\d+\.?\d*\w+.*))?$', item["item"].strip())
            if match:
                name = match.group(1).strip() or "Сорт"
                price_part = match.group(2)
                if price_part:
                    assortment_text += f"<b>{name}</b>\n💲 {price_part}\n\n"
                else:
                    assortment_text += f"<b>{name}</b>\n\n"
        assortment_text = assortment_text.rstrip("\n")
    else:
        assortment_text = "Нет ассортимента"

    extra_text = f"\n{shop['extra_text']} 🛵" if shop["extra_text"] else ""
    message_text = (
        f"<b>🏬 Магазин: <b>{shop_name}</b></b>\n\n"
        f"<b>📋 Ассортимент: 🛍</b>\n\n"
        f"{assortment_text}\n"
        f"➖➖➖➖➖\n"
        f"{extra_text}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if shop.get("contacts") and shop["contacts"] and shop["contacts"][0]:
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

# Обработка кнопки "Другие города"
@router.callback_query(F.data == "cities_countries")
async def show_cities(callback: CallbackQuery):
    logger.info(f"Processing 'cities_countries' callback for user {callback.from_user.id}")
    await callback.message.delete()
    try:
        await callback.message.answer(
            "<b>🧭 Выберите город:</b>",
            reply_markup=get_cities_menu(),
            parse_mode="HTML"
        )
        logger.info(f"Sent cities menu for user {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Failed to send cities menu: {str(e)}")
    await callback.answer()

# Обработка пагинации городов
@router.callback_query(F.data.startswith("cities_page_"))
async def change_cities_page(callback: CallbackQuery):
    page = int(callback.data.replace("cities_page_", ""))
    await callback.message.delete()
    await callback.message.answer("<b>🧭 Выберите город:</b>", reply_markup=get_cities_menu(page), parse_mode="HTML")
    logger.info(f"User {callback.from_user.id} changed cities page to {page}")
    await callback.answer()

# Обработка выбора города
@router.callback_query(F.data.startswith("city_"))
async def select_city(callback: CallbackQuery):
    order = int(callback.data.replace("city_", ""))
    try:
        with open('city.json', 'r', encoding='utf-8') as f:
            cities = json.load(f)
            city = next((c for c in cities if c["order"] == order), None)
        with open('city_shops.json', 'r', encoding='utf-8') as f:
            shops = [s for s in json.load(f) if s.get("city_order") == order]
    except FileNotFoundError:
        logger.error("city.json or city_shops.json not found")
        city = None
        shops = []
    except json.JSONDecodeError:
        logger.error("Invalid JSON in city.json or city_shops.json")
        city = None
        shops = []

    if not city:
        await callback.message.delete()
        await callback.message.answer(
            "<b>❌ Город не найден!</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="cities_countries")]
            ]),
            parse_mode="HTML"
        )
        logger.error(f"City with order {order} not found for user {callback.from_user.id}")
        await callback.answer()
        return

    if shops:
        await callback.message.delete()
        await callback.message.answer(
            f"<b>🧭 Город: {city['name']}</b>\n\n<b>📋 Доступные магазины:</b>",
            reply_markup=get_city_shops_menu(order),
            parse_mode="HTML"
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            f"<b>🧭 Город: {city['name']}</b>\n\n<b>📋 Магазины не найдены</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="cities_countries")]
            ]),
            parse_mode="HTML"
        )
    logger.info(f"User {callback.from_user.id} selected city: {city['name']}")
    await callback.answer()

# Обработка пагинации магазинов города
@router.callback_query(F.data.startswith("shops_page_"))
async def change_city_shops_page(callback: CallbackQuery):
    parts = callback.data.replace("shops_page_", "").split("_")
    city_order = int(parts[0])
    page = int(parts[1])
    try:
        with open('city.json', 'r', encoding='utf-8') as f:
            cities = json.load(f)
            city = next((c for c in cities if c["order"] == city_order), None)
    except FileNotFoundError:
        logger.error("city.json not found")
        city = None
    except json.JSONDecodeError:
        logger.error("Invalid JSON in city.json")
        city = None

    if not city:
        await callback.message.delete()
        await callback.message.answer(
            "<b>❌ Город не найден!</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="cities_countries")]
            ]),
            parse_mode="HTML"
        )
        logger.error(f"City with order {city_order} not found for user {callback.from_user.id}")
        await callback.answer()
        return

    await callback.message.delete()
    await callback.message.answer(
        f"<b>🧭 Город: {city['name']}</b>\n\n<b>📋 Доступные магазины:</b>",
        reply_markup=get_city_shops_menu(city_order, page),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} changed shops page to {page} in city {city['name']}")
    await callback.answer()

def register_handlers(dp):
    dp.include_router(router)
