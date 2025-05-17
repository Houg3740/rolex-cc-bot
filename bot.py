import logging
import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# --- Configuration ---
TOKEN = os.getenv("BOT_TOKEN")
USDT_ADDRESS = os.getenv("USDT_ADDRESS")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
PRODUCTS_FILE = "products.txt"
HISTORY_FILE = "history.txt"
PRODUCT_PRICE = 6.00

# --- Logging ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Utilities ---
def get_balance(address):
    try:
        url = f"https://apilist.tronscanapi.com/api/account?address={address}"
        res = requests.get(url)
        data = res.json()
        tokens = data.get("tokenBalances", [])
        for token in tokens:
            if token.get("tokenName") == "USDT":
                return float(token.get("balance", 0)) / 1e6
        return 0
    except Exception as e:
        logger.error(f"Balance check failed: {e}")
        return 0

def pop_product():
    with open(PRODUCTS_FILE, "r") as file:
        lines = file.readlines()
    if not lines:
        return None
    product = lines[0].strip()
    with open(PRODUCTS_FILE, "w") as file:
        file.writelines(lines[1:])
    return product

def get_remaining_count():
    with open(PRODUCTS_FILE, "r") as file:
        return len(file.readlines())

def log_history(chat_id, product):
    with open(HISTORY_FILE, "a") as file:
        file.write(f"{chat_id}: {product}\n")

def get_history(chat_id):
    if not os.path.exists(HISTORY_FILE):
        return "No history available."
    with open(HISTORY_FILE, "r") as file:
        lines = [line for line in file.readlines() if line.startswith(str(chat_id))]
    return "\n".join(lines) if lines else "No purchases found."

# --- Bot Actions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Buy Product ($6)", callback_data="buy")],
        [InlineKeyboardButton("Check Payment Status", callback_data="check")],
        [InlineKeyboardButton("Remaining Stock", callback_data="stock")],
        [InlineKeyboardButton("Purchase History", callback_data="history")],
        [InlineKeyboardButton("Contact Support", url="https://t.me/support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Please choose an option:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == "buy":
        context.user_data['initial_balance'] = get_balance(USDT_ADDRESS)
        await query.message.reply_text(
            f"To receive your product, send **{PRODUCT_PRICE} USDT** to the address below (TRC20):\n\n{USDT_ADDRESS}\n\nOnce sent, click 'Check Payment Status' again.",
            parse_mode="Markdown"
        )

    elif query.data == "check":
        current = get_balance(USDT_ADDRESS)
        initial = context.user_data.get('initial_balance', current)
        if current >= initial + PRODUCT_PRICE:
            product = pop_product()
            if product:
                log_history(chat_id, product)
                await query.message.reply_text(f"✅ Payment received. Here is your product:\n\n{product}")
            else:
                await query.message.reply_text("❌ Out of stock.")
        else:
            await query.message.reply_text("⏳ Payment not detected yet. Try again shortly.")

    elif query.data == "stock":
        count = get_remaining_count()
        await query.message.reply_text(f"📦 {count} products remaining.")

    elif query.data == "history":
        history = get_history(chat_id)
        await query.message.reply_text(f"🧾 Your purchase history:\n{history}")

# --- Admin Commands ---
async def test_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Unauthorized.")
    product = pop_product()
    if product:
        log_history(update.effective_user.id, product)
        await update.message.reply_text(f"[TEST] Product delivered: {product}")
    else:
        await update.message.reply_text("[TEST] No products available.")

async def full_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("Unauthorized.")
    with open(PRODUCTS_FILE, "r") as file:
        stock = file.read()
    await update.message.reply_text(f"📄 Stock file content:\n{stock}")

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_purchase))
    app.add_handler(CommandHandler("fullstock", full_stock))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()
