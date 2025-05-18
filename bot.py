import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
USDT_ADDRESS = os.getenv("USDT_ADDRESS")
PRODUCTS_FILE = "products.txt"
HISTORY_FILE = "history.txt"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "buy":
        await buy(update, context)
    elif data == "confirm":
        await confirm(update, context)
    elif data == "history":
        await history(update, context)
    elif data == "feedback":
        await feedback(update, context)
    elif data == "status":
        await status(update, context)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    usdt_amount = 6.00
    context.chat_data['expected_amount'] = usdt_amount
    try:
        balance = get_balance(USDT_ADDRESS)
        context.chat_data['initial_balance'] = balance
    except Exception as e:
        logger.error(f"Price error: {e}")
        await context.bot.send_message(chat_id=chat_id, text="❌ Could not retrieve USDT balance.")
        return
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"""
To receive your product, please send **{usdt_amount} USDT** (TRC20 network)

To the following address:
`{USDT_ADDRESS}`

Once you have sent the payment, use the command /confirm to verify it.
""",
        parse_mode="Markdown"
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    expected = context.chat_data.get("expected_amount")
    initial = context.chat_data.get("initial_balance")

    if expected is None or initial is None:
        await update.message.reply_text("Please use /buy before confirming.")
        return

    new_balance = get_balance(USDT_ADDRESS)
    if new_balance >= initial + expected:
        product = pop_product()
        if product:
            context.chat_data["last_product"] = product
            log_history(chat_id, product)
            await update.message.reply_text(f"✅ Payment confirmed! Here's your product:\n{product}")
        else:
            await update.message.reply_text("🚫 Out of stock.")
    else:
        await update.message.reply_text("❗Payment not detected yet. Try again shortly.")

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    product = context.chat_data.get("last_product")
    if product:
        await update.message.reply_text(f"📦 Your last product:
{product}")
    else:
        await update.message.reply_text("ℹ️ You have not received any product yet.")

async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✉️ Send your feedback directly by replying to this message.")
    return

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is online and operational.")

def get_balance(address):
    return 100  # Dummy value for development

def pop_product():
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            lines = f.readlines()
        if not lines:
            return None
        product = lines[0].strip()
        with open(PRODUCTS_FILE, 'w') as f:
            f.writelines(lines[1:])
        return product
    except FileNotFoundError:
        return None

def log_history(user_id, product):
    with open(HISTORY_FILE, 'a') as f:
        f.write(f"{user_id}: {product}\n")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
