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

# --- SETTINGS MENU ---
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👦 Gender 👧", callback_data="menu_gender")],
        [InlineKeyboardButton("📅 Age", callback_data="menu_age")],
        [InlineKeyboardButton("🌍 Language", callback_data="menu_lang")],
        [InlineKeyboardButton("👥 Partner Gender", callback_data="menu_target")]
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

# --- BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in user_data: user_data[user_id] = {'gender': 'N/A', 'age': 'N/A', 'lang': 'Hindi', 'target': 'Both'}
    
    await query.answer()
    data = query.data

    # Main Menu Options
    if data == "menu_gender":
        kb = [[InlineKeyboardButton("Male 👦", callback_data="set_G_Male"), InlineKeyboardButton("Female 👧", callback_data="set_G_Female")]]
        await query.edit_message_text("Aapka Gender kya hai?", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data == "menu_age":
        # Age selection buttons
        kb = [
            [InlineKeyboardButton("18-22", callback_data="set_A_18-22"), InlineKeyboardButton("23-27", callback_data="set_A_23-27")],
            [InlineKeyboardButton("28-35", callback_data="set_A_28-35"), InlineKeyboardButton("35+", callback_data="set_A_35+")]
        ]
        await query.edit_message_text("Apni Age Range select karein:", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "menu_lang":
        kb = [[InlineKeyboardButton("Hindi 🇮🇳", callback_data="set_L_Hindi"), InlineKeyboardButton("English 🇺🇸", callback_data="set_L_English")]]
        await query.edit_message_text("Language select karein:", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "menu_target":
        kb = [[InlineKeyboardButton("Males 👦", callback_data="set_T_Male"), InlineKeyboardButton("Females 👧", callback_data="set_T_Female")]]
        await query.edit_message_text("Aap kisse baat karna chahte hain?", reply_markup=InlineKeyboardMarkup(kb))

    # Saving Data
    elif data.startswith("set_"):
        parts = data.split("_") # e.g., ['set', 'G', 'Male']
        category = parts[1]
        value = parts[2]

        if category == 'G': user_data[user_id]['gender'] = value
        if category == 'A': user_data[user_id]['age'] = value
        if category == 'L': user_data[user_id]['lang'] = value
        if category == 'T': user_data[user_id]['target'] = value

        await query.edit_message_text(f"✅ Preference updated: {value}!\n\nUse /settings to change more.")

# --- BASIC FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['🚀 Find a partner'], ['⚙️ Settings', '🚫 Stop']]
    await update.message.reply_text(
        "👋 Welcome! Use <b>Settings</b> to set up your profile first.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True),
        parse_mode='HTML'
    )

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats: return
    
    # Filter matching logic
    my_pref = user_data.get(user_id, {'gender': 'N/A', 'target': 'Both', 'lang': 'Hindi'})
    
    for partner_id in searching_users:
        p_pref = user_data.get(partner_id, {'gender': 'N/A', 'target': 'Both', 'lang': 'Hindi'})
        
        # Simple Match: Language and Gender Target match
        if my_pref['lang'] == p_pref['lang']:
            if my_pref['target'] == p_pref['gender'] or my_pref['target'] == 'Both':
                searching_users.remove(partner_id)
                active_chats[user_id] = partner_id
                active_chats[partner_id] = user_id
                await context.bot.send_message(chat_id=user_id, text="✅ Partner Found! Say Hello.")
                await context.bot.send_message(chat_id=partner_id, text="✅ Partner Found! Say Hello.")
                return

    if user_id not in searching_users:
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Searching for a partner...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        p_id = active_chats.pop(user_id)
        active_chats.pop(p_id, None)
        await update.message.reply_text("🚫 Chat ended.")
        await context.bot.send_message(chat_id=p_id, text="🚫 Your partner ended the chat.")
    elif user_id in searching_users:
        searching_users.remove(user_id)
        await update.message.reply_text("Stopped searching.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "🚀 Find a partner":
        await search(update, context)
    elif text == "⚙️ Settings":
        await settings(update, context)
    elif text == "🚫 Stop":
        await stop(update, context)
    elif user_id in active_chats:
        await context.bot.send_message(chat_id=active_chats[user_id], text=text)

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    application.run_polling(drop_pending_updates=True)
                   
