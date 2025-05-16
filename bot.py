import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler

# Configuración
logging.basicConfig(level=logging.INFO)

# Variables de entorno
USDT_ADDRESS = os.getenv("USDT_ADDRESS")
TOKEN = os.getenv("TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_IDS = [ADMIN_USERNAME, '123456789']  # Puedes usar también tu ID numérico

# URLs y parámetros
BLOCKCYPHER_BASE = "https://api.blockcypher.com/v1/ltc/main/addrs/"
PRODUCTS_FILE = "products.txt"
BACKUP_FILE = "products_backup.txt"
REQUIRED_USD = 6.00

user_history = {}


import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler

# Configuración
logging.basicConfig(level=logging.INFO)

# Variables de entorno
USDT_ADDRESS = os.getenv("USDT_ADDRESS")
TOKEN = os.getenv("TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_IDS = [ADMIN_USERNAME, '123456789']  # Puedes usar también tu ID numérico

# URLs y parámetros
BLOCKCYPHER_BASE = "https://api.blockcypher.com/v1/ltc/main/addrs/"
PRODUCTS_FILE = "products.txt"
BACKUP_FILE = "products_backup.txt"
REQUIRED_USD = 6.00

user_history = {}

async def start(update: Update, context: CallbackContext):
    welcome_message = (
        "👋 *Welcome to RolexCCstore!*\n\n"
        "🛍️ Here’s what you can do:\n\n"
        "/buy – Start the purchase process\n"
        "/confirm – Confirm your payment\n"
        "/stock – See how many products remain\n"
        "/history – View your last product received\n"
        "/testmode – Receive a test product (free)\n"
        "/feedback – Send feedback to the admin\n"
        "/status – Check if the bot is online\n"
        "/help – Show all available commands\n"
    )
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

    keyboard = [[InlineKeyboardButton("Buy Info ($6)", callback_data='buy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose an option below:", reply_markup=reply_markup)

    keyboard = [[InlineKeyboardButton("Buy Info ($6)", callback_data='buy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose an option below:", reply_markup=reply_markup)

async def buy(update: Update, context: CallbackContext):
    await initiate_purchase(update.effective_chat.id, context)

async def initiate_purchase(chat_id, context: CallbackContext):
    usdt_amount = 6.00  # Monto fijo en USDT

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"To receive your product, please send **{usdt_amount} USDT** (TRC20 network)\n\n"
            f"to the following address:\n\n"
            f"`{USDT_ADDRESS}`\n\n"
            "Once you have sent the payment, use the command /confirm to verify it."
        ),
        parse_mode="Markdown"
    )

    context.chat_data['expected_amount'] = usdt_amount
    context.chat_data['initial_balance'] = get_balance(USDT_ADDRESS)

    except Exception as e:
    logging.error(f"Price error: {e}")
    await context.bot.send_message(chat_id=chat_id, text="❌ Could not retrieve USDT balance.")
    else:
        await update.message.reply_text("ℹ️ You have not received any product yet.")

async def testmode(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    product = pop_product()
    if product:
        user_history[chat_id] = product
        await update.message.reply_text(
            f"🧪 Test mode activated!\n\n{product}"
        )
    else:
        await update.message.reply_text("⚠️ No stock available for testing.")

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "buy":
        await initiate_purchase(query.message.chat_id, context)

def get_balance(address):
    try:
        url = f"{BLOCKCYPHER_BASE}{address}/balance"
        res = requests.get(url)
        return res.json().get("total_received", 0) / 1e8
    except Exception as e:
        logging.error(f"Balance error: {e}")
        return 0

def pop_product():
    try:
        with open(PRODUCTS_FILE, 'r') as file:
            lines = file.readlines()
        if not lines:
            return None
        product = lines[0].strip()
        with open(PRODUCTS_FILE, 'w') as file:
            file.writelines(lines[1:])
        return product
    except Exception as e:
        logging.error(f"Pop product error: {e}")
        return None

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("adminstock", adminstock))
    app.add_handler(CommandHandler("reload", reload))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("clearhistory", clearhistory))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("testmode", testmode))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
