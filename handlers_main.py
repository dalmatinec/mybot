from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import random
import logging
import os
import asyncio
from datetime import timedelta, datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = Router()

# Импорт данных
from config import CHANNEL_LINK, SUPPORT_GROUP_ID
from database import add_user, is_banned, ban_user

# Функция для создания главного меню
def get_main_menu():
    if not CHANNEL_LINK.startswith(('http://', 'https://')):
        logging.warning(f"CHANNEL_LINK '{CHANNEL_LINK}' is not a valid URL. Using default Telegram link.")
        channel_url = "https://t.me/PiratesMarket"
    else:
        channel_url = CHANNEL_LINK

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Рекомендации", callback_data="recommendations")],
        [
            InlineKeyboardButton(text="🗂 Выбрать магазин", callback_data="shops"),
            InlineKeyboardButton(text="🚀 Экспресс покупка", callback_data="express")
        ],
        [
            InlineKeyboardButton(text="🧭 Другие города", callback_data="cities_countries"),
            InlineKeyboardButton(text="💼 Работа", callback_data="work")
        ],
        [
            InlineKeyboardButton(text="⚙ Тех. поддержка", callback_data="support"),
            InlineKeyboardButton(text="🔗 Наши ссылки", url=channel_url)
        ]
    ])
    return keyboard

def get_welcome_text(user: User):
    full_name = user.full_name
    return (
        f"<b>🏴‍☠ Добро пожаловать, <a href='tg://user?id={user.id}'><b>{full_name}</b></a>!</b>\n\n"
        f"<b>Pirates Market</b> — специализированный маркетплейс для поиска органики.\n\n"
        f"🥷 <b>Анонимный и безопасный поиск</b>\n"
        f"🚀 <b>Экспресс Покупки в 2 клика</b>\n"
        f"🕒 <b>Поддержка 24/7</b>\n"
        f"✅ <b>Только проверенные магазины</b>\n\n"
        f"         <b>Более 3х лет на рынке</b>\n\n"
        f"<b>Выберите нужный раздел чтобы начать</b>"
    )

# Обработчик команды /start
@router.message(CommandStart())
async def start_command(message: Message):
    if message.chat.type != "private":
        await message.answer("<b>⛔ Эта команда доступна только в личных сообщениях!</b>", parse_mode="HTML")
        return
    if is_banned(message.from_user.id):
        await message.answer("<b>⛔ Вы заблокированы и не можете использовать бота!</b>", parse_mode="HTML")
        return
    add_user(message.from_user.id, message.from_user.username)
    logger.info(f"User {message.from_user.id} started the bot")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Мне есть 18 ✅", callback_data="age_yes"),
            InlineKeyboardButton(text="Мне нет 18 ❌", callback_data="age_no")
        ]
    ])
    if os.path.exists("media/captcha.jpg"):
        photo = FSInputFile("media/captcha.jpg")
        await message.answer_photo(
            photo=photo,
            caption="<b>Сервис предназначен для лиц старше 18 лет 🔞</b>\n\n<b>Что бы продолжить, подтвердите ваш возраст</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "<b>Сервис предназначен для лиц старше 18 лет 🔞</b>\n\n<b>Что бы продолжить, подтвердите ваш возраст</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

# Обработка выбора возраста
@router.callback_query(F.data == "age_yes")
async def age_yes_handler(callback: CallbackQuery):
    await callback.message.delete()
    if os.path.exists("media/start.jpg"):
        photo = FSInputFile("media/start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption=get_welcome_text(callback.from_user),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            get_welcome_text(callback.from_user),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    logger.info(f"User {callback.from_user.id} confirmed age 18+")

@router.callback_query(F.data == "age_no")
async def age_no_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    ban_until = datetime.now() + timedelta(hours=24)
    ban_user(user_id, ban_until)
    await callback.message.delete()
    await callback.message.answer(
        "<b>🚫 Доступ запрещён!</b>\n\nВы подтвердили, что вам нет 18.\nСогласно правилам, вы были заблокированы",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Это ошибка", callback_data="report_error")]
        ]),
        parse_mode="HTML"
    )
    logger.info(f"User {user_id} blocked for 24 hours due to age < 18")

# Обработка ошибки капчи
@router.callback_query(F.data == "report_error")
async def report_error_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or str(user_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_message = (
        f"<b>#ОшибкаКапчи</b>\n\n"
        f"<b>📅 {timestamp}</b>\n"
        f"<b>👤 @{username} (ID: {user_id})</b>\n"
        f"<b>Сообщение:</b> Пользователь сообщает об ошибке капчи, заблокирован по возрасту."
    )
    from config import SUPPORT_GROUP_ID
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Разбанить", callback_data=f"unban_{user_id}")]
    ])
    await callback.bot.send_message(SUPPORT_GROUP_ID, error_message, reply_markup=keyboard, parse_mode="HTML")
    await callback.message.edit_text(
        "<b>✅ Уведомление отправлено в поддержку. Ожидайте ответа.</b>",
        reply_markup=None,
        parse_mode="HTML"
    )
    logger.info(f"User {user_id} reported captcha error")

# Обработка возврата в главное меню
@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.message.delete()
    if os.path.exists("media/start.jpg"):
        photo = FSInputFile("media/start.jpg")
        await callback.message.answer_photo(
            photo=photo,
            caption=get_welcome_text(callback.from_user),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            get_welcome_text(callback.from_user),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    logger.info(f"User {callback.from_user.id} returned to main menu")
    await callback.answer()

def register_handlers(dp):
    dp.include_router(router)
