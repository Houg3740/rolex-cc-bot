import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Buy Info ($6)", callback_data="buy")],
        [InlineKeyboardButton("Confirm Payment", callback_data="confirm")],
        [InlineKeyboardButton("History", callback_data="history")],
        [InlineKeyboardButton("Feedback", callback_data="feedback")],
        [InlineKeyboardButton("Status", callback_data="status")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        """
👋 Welcome to RolexCCstore!

🎁 Here’s what you can do:

/buy – Start the purchase process
/confirm – Confirm your payment
/history – View your last product received
/feedback – Send feedback to the admin
/status – Check if the bot is online
""",
        reply_markup=reply_markup
    )
async def buy(update: Update, context: CallbackContext):
    await initiate_purchase(update.effective_chat.id, context)

async def initiate_purchase(chat_id, context: CallbackContext):
    try:
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

async def confirm(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    current_balance = get_balance(USDT_ADDRESS)
    initial_balance = context.chat_data.get('initial_balance', current_balance)
    if current_balance >= initial_balance + REQUIRED_USD:
        product = pop_product()
        if product:
            user_history[chat_id] = product
            await update.message.reply_text(f"✅ Payment confirmed! Here is your product:\n\n{product}")
        else:
            await update.message.reply_text("❌ No products available.")
    else:
        await update.message.reply_text("⏳ Payment not detected yet. Try again later.")

async def history(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in user_history:
        await update.message.reply_text(f"📜 Your last product:\n{user_history[chat_id]}")
    else:
        await update.message.reply_text("ℹ️ You have not received any product yet.")

async def feedback(update: Update, context: CallbackContext):
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("✍️ Please send feedback like: /feedback Your message here")
        return
    await context.bot.send_message(
        chat_id=ADMIN_USERNAME,
        text=(
            f"📢 Feedback from @{update.effective_user.username}:\n\n"
            f"{message}"
        )
    )
    await update.message.reply_text("✅ Feedback sent. Thank you!")

async def status(update: Update, context: CallbackContext):
    await update.message.reply_text("✅ Bot is running correctly.")

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

    chat_id = query.message.chat.id  # Asegúrate que sea .id, no solo chat

    if query.data == "buy":
        await initiate_purchase(chat_id, context)
    elif query.data == "confirm":
        await confirm(update, context)
    elif query.data == "history":
        await history(update, context)
    elif query.data == "feedback":
        await query.message.reply_text("✍️ Please use /feedback followed by your message.")
    elif query.data == "status":
        await query.message.reply_text("✅ Bot is running correctly.")
    else:
        await query.message.reply_text("❓ Unknown option.")

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
    app.add_handler(CommandHandler("testmode", testmode))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
