import logging
import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- KEEP ALIVE SECTION START ---
# Iska naam 'app' hona chahiye Render ke liye
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Online!"

def run_flask():
    # Render se port uthane ke liye
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
# --- KEEP ALIVE SECTION END ---

TOKEN = '8565226350:AAF97KTjahHDUuh89N9wmedklyWUflRD6UQ'

searching_users = []
active_chats = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['/search', '/stop']]
    await update.message.reply_text(
        "👋 Welcome to World Stranger Chat!\n\n"
        "Click /search to find someone to talk to.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        await update.message.reply_text("❌ You are already in a chat. Use /stop first.")
        return
    if user_id in searching_users:
        await update.message.reply_text("⏳ Still searching for a partner...")
        return
    if searching_users:
        partner_id = searching_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        await context.bot.send_message(chat_id=user_id, text="✅ Partner found! Say hello.")
        await context.bot.send_message(chat_id=partner_id, text="✅ Partner found! Say hello.")
    else:
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Searching for a stranger...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await update.message.reply_text("🚫 Chat ended.")
        await context.bot.send_message(chat_id=partner_id, text="🚫 Your partner ended the chat.")
    elif user_id in searching_users:
        searching_users.remove(user_id)
        await update.message.reply_text("Stopped searching.")
    else:
        await update.message.reply_text("You are not in a chat.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("❌ You are not connected. Click /search to find someone.")

if __name__ == '__main__':
    # Web server start karein
    keep_alive()
    
    # Bot build aur run karein
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    
    print("Bot is running...")
    application.run_polling()
        
