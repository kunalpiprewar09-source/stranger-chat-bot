import logging, os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# --- RENDER KEEP ALIVE ---
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- BOT CONFIG ---
TOKEN = '8565226350:AAGor5G0jaCarsylmJJcjFne9htebRLv2bk'
user_data = {} 
active_chats = {}
searching_users = []

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- SETTINGS MENU (Jaisa screenshot mein hai) ---
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👦 Gender 👧", callback_data="set_gender")],
        [InlineKeyboardButton("📅 Age", callback_data="set_age")],
        [InlineKeyboardButton("🌍 Language", callback_data="set_lang")],
        [InlineKeyboardButton("📍 Place", callback_data="set_place")],
        [InlineKeyboardButton("👥 Partner Gender", callback_data="set_target")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "<b>Choose settings you would like to change:</b>\n\n"
        "<i>Note: you will only be matched with users based on these preferences.</i>"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

# Button clicks handle karne ke liye
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "set_gender":
        kb = [[InlineKeyboardButton("Male", callback_data="G_M"), InlineKeyboardButton("Female", callback_data="G_F")]]
        await query.edit_message_text("Aapka gender kya hai?", reply_markup=InlineKeyboardMarkup(kb))
    
    # Isi tarah baaki buttons ke functions yahan add honge...
    elif query.data.startswith("G_"):
        gender = "Male" if query.data == "G_M" else "Female"
        user_id = query.from_user.id
        if user_id not in user_data: user_data[user_id] = {}
        user_data[user_id]['gender'] = gender
        await query.edit_message_text(f"✅ Gender set to {gender}!")

# --- BASIC FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['🚀 Find a partner'], ['⚙️ Settings', '🚫 Stop']]
    await update.message.reply_text(
        "👋 Welcome to Anonymous Chat!",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🚀 Find a partner":
        await update.message.reply_text("🔎 Searching...")
    elif text == "⚙️ Settings":
        await settings(update, context)
    elif update.effective_user.id in active_chats:
        await context.bot.send_message(chat_id=active_chats[update.effective_user.id], text=text)

# --- MAIN START ---
if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    print("Bot is starting...")
    application.run_polling(drop_pending_updates=True)
    
