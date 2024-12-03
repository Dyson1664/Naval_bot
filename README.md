# Naval Quotes Telegram Bot

A Flask-based web application that integrates with the Telegram API to send daily quotes from Naval Ravikant. Users can interact with the bot through Telegram to subscribe or unsubscribe from receiving daily quotes, and subscriber data is seamlessly managed using Google Sheets.
## Features
* **Daily Quotes**: Sends a daily quote to all subscribers at a specified time.
* **Telegram Bot Integration**: Users can interact with the bot via Telegram commands such as /subscribe and /unsubscribe.* **Google Sheets Integration**: Stores and retrieves subscriber data from a Google Sheet.
* **Google Sheets Integration**: Subscriber data is securely stored and managed using Google Sheets API.
* **Web Interface**: Displays a random quote on a web page served by Flask.
* **Cross-Platform Deployment**: Can be run on Raspberry Pi or any machine running Linux, macOS, or Windows.
  
## Prerequisites

* **Python**: 3.7 or higher
* **Telegram Bot Token**: Obtain from BotFather
* **Google Service Account Credentials**: For accessing Google Sheets API
* **Raspberry Pi (optional)**: The bot can run on a Raspberry Pi or any machine running Linux, macOS, or Windows
* **Environment Variables**: For configuration details

## Installation

### 1. Clone the Repository:
```
git clone https://github.com/dyson1664/naval_bot.git
cd naval_bot
```

### 2. Create a Virtual Environment
```
python3 -m venv venv
venv\Scripts\activate
```

## 2. Install Dependencies
```
pip install -r requirements.txt
```

## 3. Set Up Environment Variables

Create a .env file with the following variables:
```
TELEGRAM_BOT_TOKEN=your-telegram-bot-token from BotFather.
GOOGLE_CREDENTIALS=your-base64-encoded-google-credentials-json\
```

## Prepare the Google Sheet

* Create a Google Sheet named naval_bot (or change the name in the code).
* Share the sheet with your service account email.

## Running the Application
```python main.py```


## Telegram Commands
* **Bot name:** @Naval_bot_bot
* **/start or any interaction message** Display a welcome message with instructions.
* **/subscribe:** Subscribe to receive daily quotes.
* **/unsubscribe:** Unsubscribe from daily quotes.
Accessing the Web Interface
Open your web browser and navigate to:
```
http://localhost:5000 to view a random quote.
```

## Configuration
Scheduled Time for Daily Quotes: Adjust the time in  **main.py:**
```
application.job_queue.run_daily(
    send_daily_quotes,
    time=datetime.time(hour=11, minute=30, second=0)
)
