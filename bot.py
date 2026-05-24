import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DATA_FILE = "data.json"

DEFAULT_DATA = {
    "services": "Услуги Zaur Academy\n\n- Курсы по созданию Telegram ботов\n- Автоматизация бизнеса с AI\n- Индивидуальные консультации\n- Готовые боты под ключ",
    "prices": "Цены Zaur Academy\n\n- Групповые занятия от 5000 руб/мес\n- Индивидуальные от 2500 руб/час\n- Пробное занятие - бесплатно",
    "contacts": "Контакты Zaur Academy\n\nTelegram: @zaur_academy\nEmail: info@zaur.academy\nРабочее время: пн-пт 9:00-20:00 МСК"
}

EDITING = 1

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Услуги", callback_data="services")],
        [InlineKeyboardButton("Цены", callback_data="prices")],
        [InlineKeyboardButton("Контакты", callback_data="contacts")],
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("Изменить Услуги", callback_data="edit_services")],
        [InlineKeyboardButton("Изменить Цены", callback_data="edit_prices")],
        [InlineKeyboardButton("Изменить Контакты", callback_data="edit_contacts")],
        [InlineKeyboardButton("Закрыть", callback_data="close_admin")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Добро пожаловать в Zaur Academy!\n\nМы помогаем создавать Telegram ботов и автоматизировать бизнес с помощью AI.\n\nВыберите раздел, чтобы узнать подробнее:",
        reply_markup=main_keyboard()
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "Панель администратора\n\nЧто хотите изменить?",
        reply_markup=admin_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = load_data()

    if query.data == "services":
        await query.edit_message_text(data["services"], reply_markup=main_keyboard())
    elif query.data == "prices":
        await query.edit_message_text(data["prices"], reply_markup=main_keyboard())
    elif query.data == "contacts":
        await query.edit_message_text(data["contacts"], reply_markup=main_keyboard())
    elif query.data == "close_admin":
        await query.edit_message_text("Панель закрыта.")
    elif query.data in ["edit_services", "edit_prices", "edit_contacts"]:
        if query.from_user.id != ADMIN_ID:
            return ConversationHandler.END
        section = query.data.replace("edit_", "")
        context.user_data["editing"] = section
        await query.edit_message_text(
            "Введите новый текст для раздела:\n\n" + data[section]
        )
        return EDITING

    return ConversationHandler.END

async def save_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        return ConversationHandler.END

    section = context.user_data.get("editing")
    if not section:
        return ConversationHandler.END

    data = load_data()
    data[section] = update.message.text
    save_data(data)

    await update.message.reply_text("Текст обновлён!", reply_markup=admin_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

def main() -> None:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN не установлен")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            EDITING: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(conv_handler)

    logger.info("Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
