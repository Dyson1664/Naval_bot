import logging
import os
import random
import json
import base64
import datetime
import threading
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, render_template

app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
else:
    logger.info("Telegram Bot Token loaded successfully")

# Google Sheets Setup
def setup_google_sheet():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    # Load credentials from environment variable
    creds_base64 = os.getenv('GOOGLE_CREDENTIALS')
    if not creds_base64:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not set")

    try:
        creds_json = base64.b64decode(creds_base64)
        credentials_info = json.loads(creds_json)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_info, scope
        )
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Hello!\n\n"
        "Use /subscribe to receive daily quotes.\n"
        "Use /unsubscribe to stop receiving quotes."
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_message
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if add_subscriber(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="You've subscribed!")
    else:
        await context.bot.send_message(chat_id=chat_id, text="You're already subscribed!")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if remove_subscriber(chat_id):
        await context.bot.send_message(chat_id=chat_id, text="You've been unsubscribed")
    else:
        await context.bot.send_message(chat_id=chat_id, text="You are not subscribed.")

# New function to send welcome message on any text message
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "Hello!\n\n"
        "Use /subscribe to receive daily quotes.\n"
        "Use /unsubscribe to stop receiving quotes."
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_message
    )

# Flask routes
@app.route('/')
def index():
    quote = get_random_quote()
    return render_template('index.html', quote=quote)

def get_random_quote():
    with open('quotes.txt', 'r', encoding='utf-8') as f:
        quotes = f.readlines()
    return random.choice(quotes).strip()

async def send_daily_quotes(context: ContextTypes.DEFAULT_TYPE):
    quote = get_random_quote()
    subscribers = get_subscribers()
    for chat_id in subscribers:
        try:
            await context.bot.send_message(chat_id=chat_id, text=quote)
            logger.info(f"Sent quote to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send quote to {chat_id}: {e}")

def run_flask_app():
    app.run(debug=True, use_reloader=False)

def main():
    threading.Thread(target=run_flask_app).start()

    # Initialize the bot application
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('subscribe', subscribe))
    application.add_handler(CommandHandler('unsubscribe', unsubscribe))

    # Add the message handler for all text messages that are not commands
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), send_welcome))

    # Schedule daily quotes
    application.job_queue.run_daily(
        send_daily_quotes,
        time=datetime.time(hour=11, minute=30, second=0)
    )

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
