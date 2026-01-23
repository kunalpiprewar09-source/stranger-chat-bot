import logging
import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- KEEP ALIVE ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Online!"

def run_flask():
    # Render port handle karne ke liye
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True # Isse thread main program ke saath band ho jayegi
    t.start()

# --- BOT LOGIC ---
TOKEN = '8565226350:AAF97KTjahHDUuh89N9wmedklyWUflRD6UQ'

searching_users = []
active_chats = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['/search', '/stop']]
    await update.message.reply_text(
        "👋 Welcome to World Stranger Chat!\n\nClick /search to find someone.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        await update.message.reply_text("❌ Use /stop first.")
        return
    if user_id in searching_users:
        await update.message.reply_text("⏳ Searching...")
        return
    if searching_users:
        partner_id = searching_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        await context.bot.send_message(chat_id=user_id, text="✅ Connected!")
        await context.bot.send_message(chat_id=partner_id, text="✅ Connected!")
    else:
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Searching...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await update.message.reply_text("🚫 Ended.")
        await context.bot.send_message(chat_id=partner_id, text="🚫 Ended.")
    elif user_id in searching_users:
        searching_users.remove(user_id)
        await update.message.reply_text("Stopped.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        await context.bot.send_message(chat_id=active_chats[user_id], text=update.message.text)

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    application.run_polling()
        
