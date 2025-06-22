from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import time
import logging
from aiogram.enums import ParseMode

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Определение middleware
class BanCheckMiddleware:
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id if isinstance(event, (Message, CallbackQuery)) else None
        
        event_type = "message" if isinstance(event, Message) else "callback"
        logger.info(f"[Middleware] {event_type} from user {user_id} in chat {event.chat.id if hasattr(event, 'chat') else 'N/A'}")
        
        # Проверка бана
        if user_id and await is_user_banned(user_id):
            logger.info(f"User {user_id} is banned, action blocked")
            return None
        
        return await handler(event, data)

# Хранилище банов (в реальном проекте заменить на базу данных)
banned_users = set()

async def is_user_banned(user_id):
    return user_id in banned_users

async def ban_user(user_id):
    banned_users.add(user_id)
    logger.info(f"User {user_id} banned")

async def unban_user(user_id):
    if user_id in banned_users:
        banned_users.remove(user_id)
        logger.info(f"User {user_id} unbanned")

router = Router()

# Импорт данных
from config import EXPRESS_GROUP_ID, SUPPORT_GROUP_ID
from handlers_main import get_welcome_text, get_main_menu
from database import get_user_registration_date

# Определение состояний для FSM
class ExpressState(StatesGroup):
    waiting_for_order = State()
    waiting_for_send = State()

class SupportState(StatesGroup):
    waiting_for_request = State()
    waiting_for_send = State()

class ReplyState(StatesGroup):
    waiting_for_reply = State()
    waiting_for_send_reply = State()

class ShopSupportState(StatesGroup):
    waiting_for_shop_data = State()
    waiting_for_send_shop = State()

# Функция для создания меню отправки запроса
def get_send_menu(order_text):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📤 Отправить", callback_data="send_order"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ]
    ])
    return keyboard, order_text

# Функция для создания меню информации
def get_info_menu(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ℹ️ Инфо", callback_data=f"info_{user_id[:8]}")]
    ])

# Функция для создания меню с кнопкой "Назад" (с динамическим callback)
def get_back_menu(callback_data="main_menu"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
    ])

# Обработка кнопки "Экспресс покупки"
@router.callback_query(F.data == "express")
async def start_express(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>#ЭкспрессПокупки ⚡️</b>\n\n"
        "<b>Для заказа отправьте свой запрос указав город, товар, вес и свой бюджет</b>\n\n"
        "<b><i>Например</i></b>: <i>Алматы сорт 1г 25к</i>\n"
        "<b><i>Или</i></b>: <i>Астана Гаш 2гр доставка</i>\n\n"
        "<b>Вам будут поступать предложения от наших партнёров, где вы сможете выбрать подходящий для себя вариант ✔️</b>\n\n"
        "<b>Удачных сделок 🏴‍☠</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} started express order")
    await state.set_state(ExpressState.waiting_for_order)

# Обработка ввода заказа
@router.message(ExpressState.waiting_for_order, F.content_type == "text")
async def process_express_order(message: Message, state: FSMContext):
    order_text = message.text
    await state.update_data(order_text=order_text, group_id=EXPRESS_GROUP_ID, request_type="express")
    send_menu, _ = get_send_menu(order_text)
    await message.delete()
    await message.answer(
        f"<b>🛎 Ваш заказ: </b>⚡️\n\n"
        f"{order_text}\n\n"
        f"<b>Подтвердите отправку: </b>",
        reply_markup=send_menu,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} entered express order: {order_text}")
    await state.set_state(ExpressState.waiting_for_send)

@router.message(ExpressState.waiting_for_order, ~F.content_type.in_(["text"]))
async def reject_express_order(message: Message):
    await message.answer("<b>❌ Допустим только текст!</b>", parse_mode="HTML")
    logger.info(f"User {message.from_user.id} tried to send non-text in express order")

# Обработка кнопки "Отправить" для экспресс
@router.callback_query(ExpressState.waiting_for_send, F.data == "send_order")
async def send_express_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_text = data["order_text"]
    user = callback.from_user
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 5 * 3600))  # UTC+5
    
    order_message = (
        f"<b>🔖 #НовыйЗаказ ⚡️</b>\n\n"
        f"<b>📆 {timestamp}</b>\n"
        f"<b>👤 @{user.username or user.id} (ID: {user.id})</b>\n"
        f"<b>📝 Сообщение: {order_text}</b>"
    )
    
    keyboard = get_info_menu(str(user.id))
    await callback.bot.send_message(EXPRESS_GROUP_ID, order_message, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.message.edit_text(
        "<b>📤 Отправлено ✅</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]),
        parse_mode="HTML"
    )
    logger.info(f"Express order sent by user {user.id}: {order_text}")
    await state.clear()
    await callback.answer()

# Обработка кнопки "Назад" для экспресс
@router.callback_query(ExpressState.waiting_for_send, F.data == "back_to_menu")
async def back_to_menu_express(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        get_welcome_text(callback.from_user),
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} returned to main menu from express")
    await state.clear()
    await callback.answer()

# Обработка кнопки "Тех. поддержка"
@router.callback_query(F.data == "support")
async def start_support(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>⚙ Техническая поддержка</b>\n\n"
        "<b>🕹 Выберите категорию:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Для покупателей", callback_data="support_customers")],
            [InlineKeyboardButton(text="🤝 Для магазинов", callback_data="support_shops")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} started support request")
    await state.set_state(SupportState.waiting_for_request)

# Обработка запроса "Для покупателей"
@router.callback_query(F.data == "support_customers")
async def start_support_customers(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>🛒 Для покупателей</b>\n\n"
        "<b>➖ Напишите свой вопрос/жалобу на магазин или админов нашего сервиса в текстовом формате. Вам ответят в течении 24х часов</b>\n\n"
        "<b>⚠️ Ознакомьтесь с правилами по кнопке ниже</b>\n\n"
        "<b>📤 Отправьте сообщение и нажмите 'Отправить'</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📜 Правила", callback_data="show_rules")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="support")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(SupportState.waiting_for_request)
    await state.update_data(group_id=SUPPORT_GROUP_ID, request_type="support_customers", hashtag="#Жалоба")

# Обработка запроса "Для магазинов"
@router.callback_query(F.data == "support_shops")
async def start_support_shops(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        "<b>🤝 Для магазинов</b>\n\n"
        "<b>Здравствуйте, здесь вы можете подать заявку на сотрудничество с нашим сервисом 🌐</b>\n\n"
        "<b>▫️ Название магазина, город(а), ваш ассортимент, ссылка на магазин, контакты оператора и лиц принимающих решения</b>\n\n"
        "<b>✨ Название магазина, город(а), ваш ассортимент, ссылка на магазин, контакты оператора и лиц принимающих решения</b>\n\n"
        "<b><i>Например</i></b>: <i>Пираты, Алматы Астана, Сорт, Дус, LINK, @big_brokz</i>\n\n"
        "<b>Ответ поступит не позже 24 часов с момента подачи заявки ⏳</b>\n\n"
        "<b>Будем рады сотрудничеству 🤝</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="support")]
        ]),
        parse_mode="HTML"
    )
    await state.set_state(ShopSupportState.waiting_for_shop_data)
    await state.update_data(group_id=SUPPORT_GROUP_ID, request_type="support_shops", hashtag="#Сотрудничество")

# Обработка ввода запроса в техподдержку
@router.message(SupportState.waiting_for_request, F.content_type == "text")
async def process_support_request(message: Message, state: FSMContext):
    request_text = message.text
    await state.update_data(request_text=request_text, group_id=SUPPORT_GROUP_ID, request_type="support")
    send_menu, _ = get_send_menu(request_text)
    await message.delete()
    await message.answer(
        f"<b>🛎 Ваш запрос: </b>🛠\n\n"
        f"{request_text}\n\n"
        f"<b>Подтвердите отправку: </b>",
        reply_markup=send_menu,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} entered support request: {request_text}")
    await state.set_state(SupportState.waiting_for_send)

@router.message(SupportState.waiting_for_request, ~F.content_type.in_(["text"]))
async def reject_support_request(message: Message):
    await message.answer("<b>❌ Допустим только текст!</b>", parse_mode="HTML")
    logger.info(f"User {message.from_user.id} tried to send non-text in support")

# Обработка ввода данных для магазинов
@router.message(ShopSupportState.waiting_for_shop_data, F.content_type == "text")
async def process_shop_support_data(message: Message, state: FSMContext):
    shop_data = message.text
    await state.update_data(request_text=shop_data, group_id=SUPPORT_GROUP_ID, request_type="support_shops")
    send_menu, _ = get_send_menu(shop_data)
    await message.delete()
    await message.answer(
        f"<b>🛎 Ваши данные: </b>🤝\n\n"
        f"{shop_data}\n\n"
        f"<b>Подтвердите отправку: </b>",
        reply_markup=send_menu,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} entered shop support data: {shop_data}")
    await state.set_state(ShopSupportState.waiting_for_send_shop)

@router.message(ShopSupportState.waiting_for_shop_data, ~F.content_type.in_(["text"]))
async def reject_shop_support_data(message: Message):
    await message.answer("<b>❌ Допустим только текст!</b>", parse_mode="HTML")
    logger.info(f"User {message.from_user.id} tried to send non-text in shop support")

# Обработка кнопки "Отправить" для техподдержки
@router.callback_query(SupportState.waiting_for_send, F.data == "send_order")
async def send_support_request(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    request_text = data["request_text"]
    user = callback.from_user
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 5 * 3600))  # UTC+5
    hashtag = data.get("hashtag", "#Жалоба")
    
    support_message = (
        f"<b>{hashtag} 🛠</b>\n\n"
        f"<b>📆 {timestamp}</b>\n"
        f"<b>👤 @{user.username or user.id} (ID: {user.id})</b>\n"
        f"<b>📝 Сообщение: {request_text}</b>"
    )
    
    keyboard = get_info_menu(str(user.id))
    await callback.bot.send_message(SUPPORT_GROUP_ID, support_message, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.message.edit_text(
        "<b>📤 Отправлено ✅</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]),
        parse_mode="HTML"
    )
    logger.info(f"Support request sent by user {user.id}: {request_text}")
    await state.clear()
    await callback.answer()

# Обработка кнопки "Отправить" для магазинов
@router.callback_query(ShopSupportState.waiting_for_send_shop, F.data == "send_order")
async def send_shop_support_request(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    request_text = data["request_text"]
    user = callback.from_user
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 5 * 3600))  # UTC+5
    hashtag = data.get("hashtag", "#Сотрудничество")
    
    support_message = (
        f"<b>{hashtag} 🤝</b>\n\n"
        f"<b>📆 {timestamp}</b>\n"
        f"<b>👤 @{user.username or user.id} (ID: {user.id})</b>\n"
        f"<b>📝 Сообщение: {request_text}</b>"
    )
    
    keyboard = get_info_menu(str(user.id))
    await callback.bot.send_message(SUPPORT_GROUP_ID, support_message, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.message.edit_text(
        "<b>📤 Отправлено ✅</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]),
        parse_mode="HTML"
    )
    logger.info(f"Shop support request sent by user {user.id}: {request_text}")
    await state.clear()
    await callback.answer()

# Обработка кнопки "Назад" для техподдержки
@router.callback_query(SupportState.waiting_for_send, F.data == "back_to_menu")
async def back_to_menu_support(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        get_welcome_text(callback.from_user),
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
    logger.info(f"User {callback.from_user.id} returned to main menu from support")
    await state.clear()
    await callback.answer()

# Обработка ответа на заказ или запрос (реплай в группах)
@router.message(F.reply_to_message)
async def handle_reply(message: Message):
    if message.chat.type == "private":
        reply_to = message.reply_to_message
        if reply_to and "👤" in reply_to.text and "(ID:" in reply_to.text:
            user_id_str = reply_to.text.split("(ID: ")[1].split(")")[0]
            user_id = int(user_id_str) if user_id_str.isdigit() else None

            # Ищем ID группы, откуда был изначальный ответ
            group_id = None
            if "Group:EXPRESS" in reply_to.text:
                group_id = EXPRESS_GROUP_ID
            elif "Group:SUPPORT" in reply_to.text:
                group_id = SUPPORT_GROUP_ID

            if user_id and group_id:
                sender = message.from_user.username or str(message.from_user.id)
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 5 * 3600))
                reply_message = (
                    f"<b>🔖 #ОтветПользователя 📩</b>\n\n"
                    f"<b>📆 {timestamp}</b>\n"
                    f"<b>👤 От @{sender} (ID: {message.from_user.id})</b>\n"
                    f"<b>📝 Сообщение: {message.text}</b>"
                )
                await message.bot.send_message(
                    chat_id=group_id,
                    text=reply_message,
                    parse_mode="HTML"
                )
                await message.answer("<b>📤 Ваш ответ отправлен в группу</b>", parse_mode="HTML")
                logger.info(f"Reply from user {message.from_user.id} sent to group {group_id}")
            else:
                await message.answer("<b>❌ Невозможно определить группу, откуда был изначальный ответ.</b>", parse_mode="HTML")
            return
    
    # Ограничиваем обработку только реплаями на сообщения бота
    if message.reply_to_message and message.reply_to_message.from_user.id == (await message.bot.get_me()).id:
        if message.chat.id in [EXPRESS_GROUP_ID, SUPPORT_GROUP_ID]:
            reply_to = message.reply_to_message
            if "👤" in reply_to.text and "(ID:" in reply_to.text:
                user_id_str = reply_to.text.split("(ID: ")[1].split(")")[0]
                user_id = int(user_id_str) if user_id_str.isdigit() else None
                
                if user_id:
                    sender = message.from_user.username or str(message.from_user.id)
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 5 * 3600))
                    if message.chat.id == EXPRESS_GROUP_ID:
                        response_text = (
                            f"<b>🔖 #НовыйОтвет ⚡️</b>\n\n"
                            f"<b>📆 {timestamp}</b>\n"
                            f"<b>👤 От @{sender}</b>\n"
                            f"<b>📝 Сообщение: {message.text}</b>"
                        )
                        await message.bot.send_message(
                            chat_id=user_id,
                            text=response_text,
                            parse_mode="HTML"
                        )
                        await message.answer("<b>📤 Предложение отправлено ☑️</b>", parse_mode="HTML")
                        logger.info(f"Reply sent to user {user_id} from group {message.chat.id}")
                    elif message.chat.id == SUPPORT_GROUP_ID:
                        response_text = (
                            f"<b>🔖 #ОтветТехПоддержки 🛠</b>\n\n"
                            f"<b>📆 {timestamp}</b>\n"
                            f"<b>👤 От @{sender}</b>\n"
                            f"<b>📝 Сообщение: {message.text}</b>"
                        )
                        await message.bot.send_message(
                            chat_id=user_id,
                            text=response_text,
                            parse_mode="HTML"
                        )
                        await message.answer("<b>📤 Ответ отправлен ☑️</b>", parse_mode="HTML")
                        logger.info(f"Reply sent to user {user_id} from group {message.chat.id}")
                else:
                    logger.error(f"Failed to parse user ID from reply in chat {message.chat.id}")
    else:
        return  # Игнорируем все реплаи, не адресованные боту

# Обработка команды /chatid
@router.message(F.text.lower() == "/chatid", F.chat.type == "private")
async def chatid_command(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username or "Не указан"
    await message.edit_text(
        f"<b>ℹ️ Информация: 📋</b>\n👤 User ID: {user_id}\n💬 Chat ID: {chat_id}\n👤 Username: @{username}",
        parse_mode="HTML"
    )
    logger.info(f"Chat ID info requested by user {user_id}")

# Обработка команды /ban
@router.message(F.text.lower().startswith("/ban "), F.chat.type.in_(["private", "supergroup"]))
async def ban_command(message: Message):
    if message.chat.id not in [EXPRESS_GROUP_ID, SUPPORT_GROUP_ID] and message.chat.type == "supergroup":
        await message.answer("<b>❌ Данная команда доступна только в указанных группах.</b>", parse_mode="HTML")
        return
    
    try:
        user_id = int(message.text.split("/ban ")[1])
        await ban_user(user_id)
        await message.answer(f"<b>✅ Пользователь {user_id} забанен.</b>", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("<b>❌ Использование: /ban [ID]</b>", parse_mode="HTML")

# Обработка команды /unban
@router.message(F.text.lower().startswith("/unban "), F.chat.type.in_(["private", "supergroup"]))
async def unban_command(message: Message):
    if message.chat.id not in [EXPRESS_GROUP_ID, SUPPORT_GROUP_ID] and message.chat.type == "supergroup":
        await message.answer("<b>❌ Данная команда доступна только в указанных группах.</b>", parse_mode="HTML")
        return
    
    try:
        user_id = int(message.text.split("/unban ")[1])
        await unban_user(user_id)
        await message.answer(f"<b>✅ Пользователь {user_id} разбанен.</b>", parse_mode="HTML")
    except (IndexError, ValueError):
        await message.answer("<b>❌ Использование: /unban [ID]</b>", parse_mode="HTML")

# Обработка кнопки "Правила"
@router.callback_query(F.data == "show_rules")
async def show_rules(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>📜 Правила</b>\n\n"
        "<b>Если у вас возникли проблемы при покупке с одним из наших партнёров, следуйте инструкции ниже</b>\n\n"
        "<b>Правила и форма подачи жалобы :</b>\n"
        "<b>▫️ Обращаться в поддержку в случае если не удалось прояснить ситуацию самостоятельно или диспут несправедливо вынесен не в вашу пользу.</b>\n"
        "<b>▫️ Подробно описать свою проблему в одном сообщении в текстовом формате ( флуд карается баном )</b>\n"
        "<b>▫️ Сохранить скриншот переписки с продавцом и скриншот оплаты.</b>\n"
        "<b>В случае НН иметь так же фото/видео 2-3шт. Отправлять по запросу администрации ⚠️</b>\n"
        "<b>▫️ В случае оскорбления партнёров, администрация оставляет за собой право отказать в содействии.</b>\n"
        "<b>▫️ Ожидать обратной связи в течении 48 часов</b>\n\n"
        "<b>Мы понимаем каждого в такие моменты, но просим проявить терпение т.к это увеличивает ваши шансы на разрешение спорной ситуации</b>\n\n"
        "<b>С/У Администрации</b>",
        reply_markup=get_back_menu(callback_data="support_customers"),
        parse_mode="HTML"
    )
    logger.info(f"Rules shown to user {callback.from_user.id}")
    await callback.answer()

# Обработка кнопки "Назад" с динамическим возвратом
@router.callback_query(F.data.in_(["main_menu", "support", "support_customers"]))
async def back_to_previous(callback: CallbackQuery, state: FSMContext):
    if callback.data == "main_menu":
        await callback.message.delete()
        await callback.message.answer(
            get_welcome_text(callback.from_user),
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
    elif callback.data == "support":
        await callback.message.delete()
        await callback.message.answer(
            "<b>⚙ Техническая поддержка</b>\n\n"
            "<b>🕹 Выберите категорию:</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Для покупателей", callback_data="support_customers")],
                [InlineKeyboardButton(text="🤝 Для магазинов", callback_data="support_shops")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
            ]),
            parse_mode="HTML"
        )
    elif callback.data == "support_customers":
        await callback.message.delete()
        await callback.message.answer(
            "<b>🛒 Для покупателей</b>\n\n"
            "<b>➖ Напишите свой вопрос/жалобу на магазин или админов нашего сервиса в текстовом формате. Вам ответят в течении 24х часов</b>\n\n"
            "<b>⚠️ Ознакомьтесь с правилами по кнопке ниже</b>\n\n"
            "<b>📤 Отправьте сообщение и нажмите 'Отправить'</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📜 Правила", callback_data="show_rules")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="support")]
            ]),
            parse_mode="HTML"
        )
    logger.info(f"User {callback.from_user.id} returned to {callback.data}")
    await state.clear()
    await callback.answer()

def register_extra_handlers(dp):
    dp.message.middleware(BanCheckMiddleware())
    dp.include_router(router)