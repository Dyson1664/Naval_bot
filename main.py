# main.py

from flask import Flask, render_template, request
import random
import os
import logging
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
from telegram.ext import Updater, Dispatcher, CommandHandler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
else:
    logger.info("Telegram Bot Token loaded successfully")

bot = Bot(token=TELEGRAM_TOKEN)

# Google Sheets Setup
def setup_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Get the base64-encoded credentials from the environment variable
    creds_base64 = os.getenv('GOOGLE_CREDENTIALS')
    if not creds_base64:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not set")

    # Decode the base64-encoded credentials
    try:
        creds_json = base64.b64decode(creds_base64)
        credentials_info = json.loads(creds_json)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
    except Exception as e:
        logger.error(f"Error decoding Google credentials: {e}")
        raise ValueError("Invalid GOOGLE_CREDENTIALS environment variable")

    client = gspread.authorize(credentials)

    # Open your Google Sheet
    sheet = client.open('naval_bot').sheet1  # Replace 'naval_bot' with your Google Sheet name if different
    return sheet

def add_subscriber(chat_id):
    chat_id = str(chat_id)
    try:
        sheet = setup_google_sheet()
        subscribers = sheet.col_values(1)
        if chat_id not in subscribers:
            sheet.append_row([chat_id])
            logger.info(f"Added subscriber {chat_id} to Google Sheets.")
            return True
        else:
            logger.info(f"Subscriber {chat_id} already exists in Google Sheets.")
            return False
    except Exception as e:
        logger.error(f"Error adding subscriber {chat_id}: {e}")
        return False

def remove_subscriber(chat_id):
    chat_id = str(chat_id)
    try:
        sheet = setup_google_sheet()
        subscribers = sheet.col_values(1)
        if chat_id in subscribers:
            cell = sheet.find(chat_id)
            sheet.delete_rows(cell.row)
            logger.info(f"Removed subscriber {chat_id} from Google Sheets.")
            return True
        else:
            logger.info(f"Subscriber {chat_id} not found in Google Sheets.")
            return False
    except Exception as e:
        logger.error(f"Error removing subscriber {chat_id}: {e}")
        return False

def get_subscribers():
    try:
        sheet = setup_google_sheet()
        subscribers = sheet.col_values(1)
        return subscribers
    except Exception as e:
        logger.error(f"Error retrieving subscribers: {e}")
        return []

# Telegram command handlers
def start(update: Update, context):
    welcome_message = (
        "Hello! I'm your Daily Quote Bot.\n\n"
        "I can send you a new inspirational quote every day.\n\n"
        "Use /subscribe to receive daily quotes.\n"
        "Use /unsubscribe to stop receiving quotes."
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

def subscribe(update: Update, context):
    chat_id = update.effective_chat.id
    if add_subscriber(chat_id):
        context.bot.send_message(chat_id=chat_id, text="You've been subscribed to daily quotes!")
    else:
        context.bot.send_message(chat_id=chat_id, text="You're already subscribed!")

def unsubscribe(update: Update, context):
    chat_id = update.effective_chat.id
    if remove_subscriber(chat_id):
        context.bot.send_message(chat_id=chat_id, text="You've been unsubscribed from daily quotes.")
    else:
        context.bot.send_message(chat_id=chat_id, text="You are not subscribed.")

# Initialize Dispatcher
dispatcher = Dispatcher(bot, update_queue=None, workers=4, use_context=True)
# Add handlers to dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('subscribe', subscribe))
dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe))

# Flask routes
@app.route('/')
def index():
    quote = get_random_quote()
    return render_template('index.html', quote=quote)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return 'OK', 200

def set_webhook():
    webhook_url = os.getenv('WEBHOOK_URL')  # e.g., 'https://your-app.onrender.com/webhook'
    if webhook_url:
        bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
    else:
        raise ValueError("WEBHOOK_URL environment variable not set")

def get_random_quote():
    with open('quotes.txt', 'r', encoding='utf-8') as f:
        quotes = f.readlines()
    return random.choice(quotes).strip()

if __name__ == '__main__':
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        # Set up the webhook
        set_webhook()

        # Run the Flask app
        app.run(host='0.0.0.0', port=5000)
    else:
        # Polling Mode
        logger.warning("WEBHOOK_URL not set. Using polling.")

        # Initialize Updater for polling mode
        updater = Updater(token=TELEGRAM_TOKEN, use_context=True)

        # Add handlers to updater's dispatcher
        updater.dispatcher.add_handler(CommandHandler('start', start))
        updater.dispatcher.add_handler(CommandHandler('subscribe', subscribe))
        updater.dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe))

        # Start polling
        updater.start_polling()
        updater.idle()
