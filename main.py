# app.py

from flask import Flask, render_template, request
import random
import threading
import schedule
import time
import os
import logging
from dotenv import load_dotenv
from telegram import Bot, Update
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

# Initialize dispatcher as None
dispatcher = None

# File to store subscriber chat IDs
SUBSCRIBERS_FILE = 'subscribers.txt'

# Ensure subscribers file exists
if not os.path.exists(SUBSCRIBERS_FILE):
    with open(SUBSCRIBERS_FILE, 'w') as f:
        pass  # Create the file if it doesn't exist

# Helper functions
def get_random_quote():
    with open('quotes.txt', 'r', encoding='utf-8') as f:
        quotes = f.readlines()
    return random.choice(quotes).strip()

def add_subscriber(chat_id):
    chat_id = str(chat_id)
    with open(SUBSCRIBERS_FILE, 'r') as f:
        subscribers = f.read().splitlines()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        with open(SUBSCRIBERS_FILE, 'w') as f:
            f.write('\n'.join(subscribers))
        return True
    return False

def remove_subscriber(chat_id):
    chat_id = str(chat_id)
    with open(SUBSCRIBERS_FILE, 'r') as f:
        subscribers = f.read().splitlines()
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        with open(SUBSCRIBERS_FILE, 'w') as f:
            f.write('\n'.join(subscribers))
        return True
    return False

def get_subscribers():
    with open(SUBSCRIBERS_FILE, 'r') as f:
        subscribers = f.read().splitlines()
    return subscribers

# Telegram command handlers
def start(update: Update, context):
    welcome_message = (
        "Hello! I'm your Daily Quote Bot.\n\n"
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

# Flask routes
@app.route('/')
def index():
    quote = get_random_quote()
    return render_template('index.html', quote=quote)

@app.route('/webhook', methods=['POST'])
def webhook():
    global dispatcher
    if request.method == 'POST':
        update = Update.de_json(request.get_json(force=True), bot)
        if dispatcher:
            dispatcher.process_update(update)
        return 'OK', 200

def set_webhook():
    webhook_url = os.getenv('WEBHOOK_URL')  # e.g., 'https://your-app.onrender.com/webhook'
    if webhook_url:
        bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to {webhook_url}")
    else:
        logger.error("WEBHOOK_URL not set!")

# Scheduler function
def send_daily_quotes():
    quote = get_random_quote()
    subscribers = get_subscribers()
    for chat_id in subscribers:
        try:
            bot.send_message(chat_id=chat_id, text=quote)
            logger.info(f"Sent quote to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send quote to {chat_id}: {e}")

def run_scheduler():
    schedule.every().day.at("11:45").do(send_daily_quotes)  # Adjust time as needed
    while True:
        schedule.run_pending()
        time.sleep(60)  # Wait one minute

def run_flask_app():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    webhook_url = os.getenv('WEBHOOK_URL')
    if webhook_url:
        # Webhook Mode
        set_webhook()

        # Initialize Dispatcher for webhook mode
        dispatcher = Dispatcher(bot, update_queue=None, workers=4, use_context=True)
        # Add handlers to dispatcher
        dispatcher.add_handler(CommandHandler('start', start))
        dispatcher.add_handler(CommandHandler('subscribe', subscribe))
        dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe))

        # Start the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

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

        # Start the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

        # Start the Flask app in a separate thread
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()


        # Start polling
        updater.start_polling()
        updater.idle()
