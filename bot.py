import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler

# Configuración
logging.basicConfig(level=logging.INFO)

LTC_ADDRESS = os.getenv("LTC_ADDRESS")
TOKEN = os.getenv("TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

LTC_USD_URL = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd"
BLOCKCYPHER_BASE = "https://api.blockcypher.com/v1/ltc/main/addrs/"
PRODUCTS_FILE = "products.txt"
REQUIRED_USD = 6.00

# Comando /start
async def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Buy Info ($6)", callback_data='buy')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to RolexCCstore! Choose an option:", reply_markup=reply_markup)

# Manejo del botón Buy Info
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "buy":
        logging.info("User clicked Buy Info")
        try:
            price_response = requests.get(LTC_USD_URL)
            ltc_price = price_response.json().get("litecoin", {}).get("usd")

            if ltc_price is None:
                raise ValueError("Litecoin price not available.")

            ltc_amount = round(REQUIRED_USD / ltc_price, 8)

            await query.edit_message_text(
                f"To receive your information, send **{ltc_amount} LTC** to the address below:\n\n"
                f"`{LTC_ADDRESS}`\n\n"
                f"Once sent, this bot will automatically monitor and deliver your product.",
                parse_mode='Markdown'
            )

            context.job_queue.run_once(check_payment, 10, data={
                'chat_id': query.message.chat_id,
                'amount': ltc_amount,
                'initial_balance': get_balance(LTC_ADDRESS)
            })
        except Exception as e:
            logging.error(f"Error fetching LTC price: {e}")
            await query.edit_message_text("❌ Error retrieving Litecoin price. Please try again later.")

# Verificar saldo
def get_balance(address):
    url = f"{BLOCKCYPHER_BASE}{address}/balance"
    try:
        res = requests.get(url)
        return res.json().get("total_received", 0) / 1e8
    except Exception as e:
        logging.error(f"Error fetching balance: {e}")
        return 0

# Monitoreo de pago
async def check_payment(context: CallbackContext):
    job = context.job
    data = job.data
    new_balance = get_balance(LTC_ADDRESS)
    if new_balance >= data['initial_balance'] + data['amount']:
        product = pop_product()
        if product:
            await context.bot.send_message(chat_id=data['chat_id'], text=f"✅ Payment received! Here's your info:\n\n{product}")
        else:
            await context.bot.send_message(chat_id=data['chat_id'], text="Sorry, we're out of stock.")
            await context.bot.send_message(chat_id=ADMIN_USERNAME, text="Stock exhausted. Please refill products.txt.")
    else:
        context.job_queue.run_once(check_payment, 15, data=data)

# Obtener y eliminar primera línea del archivo
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
        logging.error(f"Error reading product file: {e}")
        return None

# Iniciar bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
