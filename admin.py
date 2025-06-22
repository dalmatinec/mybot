from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMINS
from database import ban_user, unban_user, get_user_count, get_shop_clicks_stats, get_all_users
from handlers_main import get_welcome_text, get_main_menu
import asyncio
import logging
import sys
from datetime import timedelta, datetime

# Глобальное логирование
global_logger = logging.getLogger('global')
global_handler = logging.FileHandler('global_logs.log', mode='a', encoding='utf-8')
global_handler.setLevel(logging.INFO)
global_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
global_logger.addHandler(global_handler)
global_logger.setLevel(logging.INFO)

# Консольный вывод для отладки
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
global_logger.addHandler(console_handler)

# Обычное логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = Router()

# Состояния для рассылки
class SendState(StatesGroup):
    waiting_for_forward = State()
    waiting_for_confirmation = State()

# Проверка на админа
def is_admin(user_id):
    global_logger.info(f"Checking admin status for user {user_id}")
    return user_id in ADMINS

# Команда /admin
@router.message(Command("admin"))
async def admin_panel(message: Message):
    global_logger.info(f"Received command /admin from user {message.from_user.id}")
    if message.chat.type != "private":
        await message.answer("<b>⛔ Доступно только в личных сообщениях!</b>", parse_mode="HTML")
        return
    if not is_admin(message.from_user.id):
        await message.answer("<b>⛔ Нет прав администратора!</b>", parse_mode="HTML")
        return
    await message.answer(
        "<b>📋 Панель администратора:</b>\n\n"
        "<b>📊 Команды:</b>\n"
        "/statistic - Статистика использования бота\n"
        "/send - Начать рассылку сообщения\n"
        "/chatid - Получить ID текущего чата\n"
        "/ban - Забанить пользователя (реплай)\n"
        "/unban - Разбанить пользователя (реплай)",
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} opened admin panel")

# Команда /chatid
@router.message(Command("chatid"))
async def get_chat_id(message: Message):
    global_logger.info(f"Received command /chatid from user {message.from_user.id}")
    if message.chat.type != "private":
        await message.answer("<b>⛔ Доступно только в личных сообщениях!</b>", parse_mode="HTML")
        return
    if not is_admin(message.from_user.id):
        await message.answer("<b>⛔ Нет прав администратора!</b>", parse_mode="HTML")
        return
    chat_id = message.chat.id
    await message.answer(f"<b>🆔 ID текущего чата: {chat_id}</b>", parse_mode="HTML")
    logger.info(f"User {message.from_user.id} requested chat ID: {chat_id}")

# Команда /statistic
@router.message(Command("statistic"))
async def show_statistics(message: Message):
    global_logger.info(f"Received command /statistic from user {message.from_user.id}")
    if message.chat.type != "private":
        await message.answer("<b>⛔ Доступно только в личных сообщениях!</b>", parse_mode="HTML")
        return
    if not is_admin(message.from_user.id):
        await message.answer("<b>⛔ Нет прав администратора!</b>", parse_mode="HTML")
        return
    user_count = get_user_count()
    shop_stats = get_shop_clicks_stats()
    
    stats_text = "<b>📊 Статистика бота:</b>\n\n"
    stats_text += f"<b>👥 Всего пользователей: {user_count}</b>\n\n"
    stats_text += "<b>🏬 Популярность магазинов (клики):</b>\n"
    if shop_stats:
        for shop, clicks in shop_stats:
            stats_text += f"{shop}: {clicks} кликов\n"
    else:
        stats_text += "Нет данных по кликам.\n"
    
    await message.answer(stats_text, parse_mode="HTML")
    logger.info(f"User {message.from_user.id} requested statistics")

# Команда /ban
@router.message(Command("ban"))
async def ban_user_command(message: Message):
    global_logger.info(f"Received command /ban from user {message.from_user.id}")
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("<b>⛔ Доступно только в группах!</b>", parse_mode="HTML")
        return
    if not is_admin(message.from_user.id):
        await message.answer("<b>⛔ Нет прав администратора!</b>", parse_mode="HTML")
        return
    if not message.reply_to_message:
        await message.answer("<b>⛔ Ответьте на сообщение пользователя для блокировки!</b>", parse_mode="HTML")
        return
    user_id = message.reply_to_message.from_user.id
    ban_user(user_id, datetime.now() + timedelta(hours=24))
    await message.answer(f"<b>⛔ Пользователь {message.reply_to_message.from_user.mention} заблокирован!</b>", parse_mode="HTML")
    logger.info(f"User {user_id} banned by admin {message.from_user.id}")

# Команда /unban
@router.message(Command("unban"))
async def unban_user_command(message: Message):
    global_logger.info(f"Received command /unban from user {message.from_user.id}")
    if message.chat.type not in ["group", "supergroup"]:
        await message.answer("<b>⛔ Доступно только в группах!</b>", parse_mode="HTML")
        return
    if not is_admin(message.from_user.id):
        await message.answer("<b>⛔ Нет прав администратора!</b>", parse_mode="HTML")
        return
    if not message.reply_to_message:
        await message.answer("<b>⛔ Ответьте на сообщение пользователя для разблокировки!</b>", parse_mode="HTML")
        return
    user_id = message.reply_to_message.from_user.id
    unban_user(user_id)
    await message.answer(f"<b>✔️ Пользователь {message.reply_to_message.from_user.mention} разблокирован!</b>", parse_mode="HTML")
    try:
        await message.bot.send_message(user_id, "<b>✔️ Ваш бан снят. Перезапустите бота командой /start.</b>", parse_mode="HTML")
        logger.info(f"Notification sent to user {user_id} after unban")
    except Exception as e:
        logger.error(f"Failed to notify user {user_id} after unban: {str(e)}")
    logger.info(f"User {user_id} unbanned by admin {message.from_user.id}")

# Обработчик кнопки "Разбанить" из техподдержки
@router.callback_query(F.data.startswith("unban_"))
async def unban_from_support(callback: CallbackQuery):
    user_id = int(callback.data.replace("unban_", ""))
    unban_user(user_id)
    await callback.message.edit_text(
        f"<b>✔️ Пользователь {user_id} разблокирован!</b>",
        reply_markup=None,
        parse_mode="HTML"
    )
    try:
        await callback.bot.send_message(user_id, "<b>✔️ Ваш бан снят. Перезапустите бота командой /start.</b>", parse_mode="HTML")
        logger.info(f"Notification sent to user {user_id} after unban from support")
    except Exception as e:
        logger.error(f"Failed to notify user {user_id} after unban from support: {str(e)}")
    await callback.answer()

# Команда /send
@router.message(Command("send"))
async def start_send(message: Message, state: FSMContext):
    global_logger.info(f"Received command /send from user {message.from_user.id}")
    if message.chat.type != "private":
        await message.answer("*⛔ Доступно только в личных сообщениях!*", parse_mode="Markdown")
        return
    if not is_admin(message.from_user.id):
        await message.answer("*⛔ Нет прав администратора!*", parse_mode="Markdown")
        return
    await message.answer(
        "*📬 Перешлите сообщение или пост для рассылки (с медиа, кнопками и текстом):*",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    logger.info(f"User {message.from_user.id} started send command with forward")
    await state.set_state(SendState.waiting_for_forward)

@router.message(SendState.waiting_for_forward)
async def process_send_forward(message: Message, state: FSMContext):
    if not message.forward_from_chat and not message.forward_from_message_id:
        await message.answer("*⛔ Пожалуйста, перешлите сообщение или пост!*", parse_mode="Markdown")
        return
    
    await state.update_data(forward_message_id=message.message_id, forward_chat_id=message.chat.id)
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_send")],
        [InlineKeyboardButton(text="🚫 Отменить", callback_data="cancel_send")]
    ])
    await message.answer(
        "*📤 Подтвердите рассылку:*",
        reply_markup=confirm_keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(SendState.waiting_for_confirmation)

@router.callback_query(SendState.waiting_for_confirmation, F.data.in_(["confirm_send", "cancel_send"]))
async def confirm_send(callback: CallbackQuery, state: FSMContext):
    if callback.data == "cancel_send":
        await callback.message.delete()
        await callback.message.answer(
            get_welcome_text(callback.from_user),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
        logger.info(f"User {callback.from_user.id} canceled broadcast")
        await state.clear()
        await callback.answer()
        return
    
    data = await state.get_data()
    message_id = data["forward_message_id"]
    chat_id = data["forward_chat_id"]
    users = get_all_users()
    
    sent_count = 0
    for user_id in users:
        try:
            await callback.bot.forward_message(
                chat_id=user_id,
                from_chat_id=chat_id,
                message_id=message_id
            )
            sent_count += 1
            await asyncio.sleep(0.05)
            logger.info(f"Message forwarded to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to forward message to user {user_id}: {str(e)}")
            continue
    
    await callback.message.delete()
    await callback.message.answer(
        f"*✔️ Рассылка завершена.*\n"
        f"*Переслато {sent_count} пользователям.*",
        parse_mode="Markdown"
    )
    logger.info(f"Broadcast completed by user {callback.from_user.id}, forwarded to {sent_count} users")
    await state.clear()
    await callback.answer()

# Регистрация обработчиков
def register_admin_handlers(dp):
    dp.include_router(router)
    logger.info("Admin handlers registered successfully")
    global_logger.info("Admin handlers registered successfully in global_logs")