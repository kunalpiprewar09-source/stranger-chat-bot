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
    text = "<b>Choose settings you would like to change:</b>"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

# --- BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    if user_id not in user_data: 
        user_data[user_id] = {'gender': 'Both', 'age': 'Any', 'lang': 'Hindi', 'target': 'Both'}
    
    await query.answer()
    data = query.data

    if data == "menu_gender":
        kb = [[InlineKeyboardButton("Male", callback_data="set_G_Male"), InlineKeyboardButton("Female", callback_data="set_G_Female")]]
        await query.edit_message_text("Aapka Gender:", reply_markup=InlineKeyboardMarkup(kb))
    elif data == "menu_target":
        kb = [[InlineKeyboardButton("Males", callback_data="set_T_Male"), InlineKeyboardButton("Females", callback_data="set_T_Female"), InlineKeyboardButton("Both", callback_data="set_T_Both")]]
        await query.edit_message_text("Kisse baat karni hai?", reply_markup=InlineKeyboardMarkup(kb))
    elif data.startswith("set_"):
        parts = data.split("_")
        user_data[user_id][parts[1] == 'G' and 'gender' or 'target' if parts[1] != 'A' else 'age'] = parts[2]
        await query.edit_message_text(f"✅ Saved: {parts[2]}")

# --- UPGRADED SEARCH LOGIC ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        await update.message.reply_text("❌ Already in chat.")
        return

    # Default data if not set
    if user_id not in user_data:
        user_data[user_id] = {'gender': 'Unknown', 'target': 'Both', 'lang': 'Hindi'}

    my_pref = user_data[user_id]

    # Try matching with waiting users
    for partner_id in searching_users[:]:
        if partner_id == user_id: continue
        
        p_pref = user_data.get(partner_id, {'gender': 'Unknown', 'target': 'Both', 'lang': 'Hindi'})

        # Match Conditions:
        # 1. My target matches their gender OR I want 'Both'
        # 2. Their target matches my gender OR they want 'Both'
        cond1 = (my_pref['target'] == p_pref['gender'] or my_pref['target'] == 'Both')
        cond2 = (p_pref['target'] == my_pref['gender'] or p_pref['target'] == 'Both')

        if cond1 and cond2:
            searching_users.remove(partner_id)
            if user_id in searching_users: searching_users.remove(user_id)
            
            active_chats[user_id] = partner_id
            active_chats[partner_id] = user_id
            
            await context.bot.send_message(chat_id=user_id, text="✅ Partner Found! Type to chat.")
            await context.bot.send_message(chat_id=partner_id, text="✅ Partner Found! Type to chat.")
            return

    if user_id not in searching_users:
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Searching... please wait.")

# --- SHARED FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['🚀 Find a partner'], ['⚙️ Settings', '🚫 Stop']]
    await update.message.reply_text("👋 Welcome!", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        p_id = active_chats.pop(user_id)
        active_chats.pop(p_id, None)
        await update.message.reply_text("🚫 Chat ended.")
        await context.bot.send_message(chat_id=p_id, text="🚫 Partner left.")
    elif user_id in searching_users:
        searching_users.remove(user_id)
        await update.message.reply_text("Stopped.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    if text == "🚀 Find a partner": await search(update, context)
    elif text == "⚙️ Settings": await settings(update, context)
    elif text == "🚫 Stop": await stop(update, context)
    elif user_id in active_chats:
        try:
            await context.bot.send_message(chat_id=active_chats[user_id], text=text)
        except:
            await stop(update, context)

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    application.run_polling(drop_pending_updates=True)
