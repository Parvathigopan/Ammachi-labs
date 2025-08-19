import csv
import os
from datetime import datetime, time, timedelta
import pytz
import db
from telegram import Update
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)

LOG_FILE_CSV = "reminder_log.csv"
LOG_FILE_JSON = "reminder_log.json"


def log_reminder(chat_id, reminder_id, reminder_time, text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_entry = {
        "timestamp": timestamp,
        "chat_id": chat_id,
        "reminder_id": reminder_id,
        "time": reminder_time,
        "text": text,
    }

    # ---- Append to CSV ----
    file_exists = os.path.isfile(LOG_FILE_CSV)
    with open(LOG_FILE_CSV, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=log_entry.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(log_entry)


load_dotenv()  # loads .env file into environment variables


# ---------- Bot Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm your Reminder Bot.\n"
        "Use /help to see available commands."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📌 Available Commands with Examples:\n\n"
        "/start - Start the bot\n"
        "Example: /start\n\n"
        "/help - Show this help message\n"
        "Example: /help\n\n"
        "/add HH:MM text - Add a daily reminder\n"
        "Example: /add 08:30 Take morning vitamins\n\n"
        "/add_once HH:MM text - Add a one-time reminder\n"
        "Example: /add_once 15:00 Attend meeting\n\n"
        "/list - Show all reminders\n"
        "Example: /list\n\n"
        "/delete <id> - Delete a reminder by its ID\n"
        "Example: /delete 3\n\n"
        "/clear - Clear all reminders\n"
        "Example: /clear\n\n"
        "/tz <Region/City> - Set your timezone\n"
        "Example: /tz Asia/Kolkata\n\n"
        "/export - Export reminder logs\n"
        "Example: /export"
    )
    await update.message.reply_text(help_text)



# --- Daily Reminder Command ---
async def add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add HH:MM text")
        return

    # Parse time and reminder text
    try:
        hhmm = context.args[0]
        text = " ".join(context.args[1:])
        hour_str, minute_str = hhmm.split(":")
        hour = int(hour_str)
        minute = int(minute_str)
        
        # Validate ranges
        if not (0 <= hour <= 23) or not (0 <= minute <= 59):
            raise ValueError("Hour must be 0–23 and minute 0–59")
    except Exception:
        await update.message.reply_text("Invalid time format. Use HH:MM (24h).")
        return

    # Get timezone for this chat
    tz = db.get_timezone(chat_id) or "Asia/Kolkata"

    # Insert reminder into DB
    rid = db.add_reminder(chat_id, hhmm, text, tz)

    # Schedule daily reminder safely
    t = time(hour=hour, minute=minute, tzinfo=pytz.timezone(tz))
    context.application.job_queue.run_daily(
        send_reminder,
        t,
        data=(chat_id, rid, text, hhmm),
        name=str(rid),
        chat_id=chat_id
    )

    await update.message.reply_text(f"✅ Daily reminder added [{rid}] {hhmm} — {text}🎯")



# --- One-time Reminder Command ---
async def reminder_callback(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    reminder_id = job.name  # unique name assigned when scheduling
    await context.bot.send_message(job.chat_id, f"⏰ Reminder: {job.data}")
    log_reminder(job.chat_id, reminder_id, job.data, job.data)



async def add_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add_once HH:MM text")
        return

    time_str = context.args[0]
    text = " ".join(context.args[1:])

    try:
        reminder_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        await update.message.reply_text("Invalid time format. Use HH:MM (24h).")
        return

    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    target_dt = tz.localize(datetime.combine(now.date(), reminder_time))

    # If time already passed today → schedule for tomorrow
    if target_dt <= now:
        target_dt += timedelta(days=1)

    delay = (target_dt - now).total_seconds()

    context.job_queue.run_once(
        reminder_callback,
        delay,
        chat_id=update.effective_chat.id,
        name=f"reminder_{time_str}_{text}",
        data=text,
    )

    await update.message.reply_text(
        f"⏰ One-time reminder set for {target_dt.strftime('%H:%M')} — {text}"
    )


# --- List Reminders ---
async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    reminders = db.get_reminders(chat_id)

    if not reminders:
        await update.message.reply_text("No daily reminders set.")
        return

    tz = db.get_timezone(chat_id) or "Asia/Kolkata"
    msg = f"Daily Reminders (Timezone: {tz}):\n"
    for r in reminders:
        msg += f"[{r[0]}] {r[1]} — {r[2]}\n"

    await update.message.reply_text(msg)


# --- Delete Reminder ---
async def delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /delete <id>")
        return

    rid = int(context.args[0])
    deleted = db.delete_reminder(rid)

    if deleted:
        await update.message.reply_text(f"🗑️  Deleted reminder [{rid}]")
    else:
        await update.message.reply_text(f"No reminder with ID {rid}")


# --- Clear Reminders ---
async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    db.clear_reminders(chat_id)
    await update.message.reply_text("🧹  Cleared all your daily reminders.")


# --- Set Timezone ---
async def tz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)

    if not context.args:
        await update.message.reply_text("Usage: /tz <IANA tz name>")
        return

    tz = context.args[0]
    if tz not in pytz.all_timezones:
        await update.message.reply_text("Invalid timezone. Example: Asia/Kolkata")
        return

    db.set_timezone(chat_id, tz)
    await update.message.reply_text(f"✅ Timezone set to {tz}")


# --- Export Log ---
async def export_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    reminders = db.get_reminders(chat_id)  # fetch all reminders for this user

    if not reminders:
        await update.message.reply_text("No reminders to export.")
        return

    # Write all reminders to CSV
    with open(LOG_FILE_CSV, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["timestamp", "chat_id", "reminder_id", "time", "text"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for r in reminders:
            rid, time_str, text = r[0], r[1], r[2]
            writer.writerow({
                "timestamp": timestamp,
                "chat_id": chat_id,
                "reminder_id": rid,
                "time": time_str,
                "text": text
            })

    # Send the CSV
    await update.message.reply_document(open(LOG_FILE_CSV, "rb"))



# ---------- Reminder Job ----------
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id, rid, text, reminder_time = job.data
    await context.bot.send_message(chat_id, f"⏰ Reminder: {text}")
    log_reminder(chat_id, rid, reminder_time, text)


def schedule_jobs(application: Application):
    """Schedule all reminders from DB into JobQueue safely."""
    all_reminders = db.get_all_reminders()
    for r in all_reminders:
        rid, chat_id, time_str, text, tz = r

        try:
            hh, mm = map(int, time_str.split(":"))
            # Validate ranges
            if not (0 <= hh <= 23) or not (0 <= mm <= 59):
                raise ValueError(f"Invalid time {time_str}")
            
            t = time(hour=hh, minute=mm, tzinfo=pytz.timezone(tz))
            application.job_queue.run_daily(
                send_reminder,
                t,
                data=(chat_id, rid, text, time_str),
                name=str(rid),
                chat_id=chat_id
            )
        except Exception as e:
            print(f"⚠ Skipping invalid reminder [{rid}] time: {e}")


# ---------- Main ----------
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # init DB
    db.init_db()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("add_once", add_once))
    app.add_handler(CommandHandler("list", list_cmd))
    app.add_handler(CommandHandler("delete", delete_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("tz", tz_cmd))
    app.add_handler(CommandHandler("export", export_cmd))

    schedule_jobs(app)
    app.run_polling()


if __name__ == "__main__":
    main()
