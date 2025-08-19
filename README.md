

# Telegram Reminder Bot

## Introduction

This project is a Telegram bot that helps users manage reminders. Users can set daily reminders or one-time reminders, view, delete, clear them, set their timezone, and export logs. The bot ensures reminders persist even after restarts by using a SQLite3 database.

## Objectives

* Allow users to set daily or one-time reminders easily.
* Keep reminders persistent across bot restarts.
* Provide timezone support for accurate scheduling.
* Enable exporting of reminders as logs for tracking.

## Tools & Technologies

* **Python** (Programming language)
* **Telegram Bot API**
* **SQLite3** (Persistence database)
* **Python Libraries:** `python-telegram-bot`, `pytz`, `dotenv`

## Features

* Add daily reminders (`/add`)
* Add one-time reminders (`/add_once`)
* List reminders (`/list`)
* Delete specific reminders (`/delete <id>`)
* Clear all reminders (`/clear`)
* Set timezone (`/tz <Region/City>`)
* Export reminders to CSV (`/export`)

## Persistence File

All reminders are stored in `persistence.db` using SQLite3, which ensures that reminders are not lost when the bot restarts.

## Example Log File

When reminders trigger, they are logged in `example_log.csv`.This is a sample log taken from bot's log file

```
timestamp,chat_id,reminder_id,time,text
2025-08-19 12:00:00,123456789,1,08:30,Take morning vitamins
```

This log helps track all reminders sent by the bot.

## Environment File (`.env`)

The bot requires a `.env` file in the project root to store sensitive information securely. At minimum, the `.env` file must contain:

```
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

* `TELEGRAM_BOT_TOKEN` – This is your Telegram bot token obtained from BotFather.
* Make sure the `.env` file is not shared publicly, as it contains private credentials.

## Installation Instructions

1. Clone the repository:

   ```
   git clone <repository_url>
   cd reminder_bot
   ```
2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```
3. Create the `.env` file as described above.
4. Initialize the database:
   
    ```
   python data.py
   ```

5. Run the bot:

   ```
   python main.py
   ```

## Usage Examples

* `/start` – Start the bot
* `/add 08:30 Take morning vitamins` – Add a daily reminder
* `/add_once 15:00 Attend meeting` – Add a one-time reminder
* `/list` – List all reminders
* `/delete 3` – Delete reminder with ID 3
* `/clear` – Clear all reminders
* `/tz Asia/Kolkata` – Set timezone
* `/export` – Export all reminders to CSV

## Conclusion

This bot helps manage reminders effectively with persistent storage, timezone support, and an easy-to-use interface. It can be used by students or professionals who want simple automated reminders on Telegram.


