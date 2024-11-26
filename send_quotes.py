# send_quotes.py

import os
import logging
from dotenv import load_dotenv
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
import random

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    creds_base64 = os.getenv('GOOGLE_CREDENTIALS')
    if not creds_base64:
        raise ValueError("GOOGLE_CREDENTIALS environment variable not set")
    try:
        creds_json = base64.b64decode(creds_base64)
        credentials_info = json.loads(creds_json)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
    except Exception as e:
        logger.error(f"Error decoding Google credentials: {e}")
        raise ValueError("Invalid GOOGLE_CREDENTIALS environment variable")
    client = gspread.authorize(credentials)
    sheet = client.open('naval_bot').sheet1  # Replace with your Google Sheet name
    return sheet

def get_random_quote():
    with open('quotes.txt', 'r', encoding='utf-8') as f:
        quotes = f.readlines()
    return random.choice(quotes).strip()

def get_subscribers():
    try:
        sheet = setup_google_sheet()
        subscribers = sheet.col_values(1)
        return subscribers
    except Exception as e:
        logger.error(f"Error retrieving subscribers: {e}")
        return []

def send_daily_quotes():
    quote = get_random_quote()
    subscribers = get_subscribers()
    for chat_id in subscribers:
        try:
            bot.send_message(chat_id=chat_id, text=quote)
            logger.info(f"Sent quote to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send quote to {chat_id}: {e}")

if __name__ == '__main__':
    send_daily_quotes()
