import logging, os
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ConversationHandler, 
    CallbackQueryHandler
)

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

# --- BOT STATES & LOGIC ---
TOKEN = '8565226350:AAGor5G0jaCarsylmJJcjFne9htebRLv2bk'

# States for Conversation
GENDER, AGE, PLACE, TARGET = range(4)

user_data = {} 
searching_users = []
active_chats = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- START & SETTINGS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['/search', '/set'], ['/stop']]
    await update.message.reply_text(
        "👋 Welcome! Pehle /set button par click karke apni profile banayein.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def set_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Male 👤", callback_data="M"),
         InlineKeyboardButton("Female 👩", callback_data="F")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Aapka Gender kya hai?", reply_markup=reply_markup)
    return GENDER

async def gender_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['gender'] = query.data
    await query.edit_message_text("Apni Age (Umar) likhein: (e.g. 22)")
    return AGE

async def age_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("Aap kahan se hain? (Shehar/Place ka naam likhein)")
    return PLACE

async def place_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['place'] = update.message.text
    keyboard = [
        [InlineKeyboardButton("Male 👤", callback_data="M"),
         InlineKeyboardButton("Female 👩", callback_data="F")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Aap kisse baat karna chahte hain? (Target Gender)", reply_markup=reply_markup)
    return TARGET

async def target_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user_data[user_id] = {
        'gender': context.user_data['gender'],
        'age': context.user_data['age'],
        'place': context.user_data['place'],
        'target': query.data
    }
    
    profile_text = (
        f"✅ Profile Saved!\n"
        f"Gender: {user_data[user_id]['gender']}\n"
        f"Age: {user_data[user_id]['age']}\n"
        f"Place: {user_data[user_id]['place']}\n"
        f"Talking to: {user_data[user_id]['target']}"
    )
    await query.edit_message_text(profile_text + "\n\nAb aap /search kar sakte hain!")
    return ConversationHandler.END

# --- SEARCH & CHAT LOGIC ---
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        await update.message.reply_text("❌ Aap pehle se chat mein hain.")
        return
    if user_id not in user_data:
        await update.message.reply_text("⚠️ Pehle /set se apni profile banayein.")
        return

    my_pref = user_data[user_id]
    for partner_id in searching_users:
        partner_pref = user_data.get(partner_id)
        if partner_pref and partner_pref['gender'] == my_pref['target'] and my_pref['gender'] == partner_pref['target']:
            searching_users.remove(partner_id)
            active_chats[user_id] = partner_id
            active_chats[partner_id] = user_id
            await context.bot.send_message(chat_id=user_id, text=f"✅ Match Found! Age: {partner_pref['age']}, From: {partner_pref['place']}")
            await context.bot.send_message(chat_id=partner_id, text=f"✅ Match Found! Age: {my_pref['age']}, From: {my_pref['place']}")
            return

    if user_id not in searching_users:
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Matching... please wait.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        p_id = active_chats.pop(user_id)
        active_chats.pop(p_id, None)
        await update.message.reply_text("🚫 Chat ended.")
        await context.bot.send_message(chat_id=p_id, text="🚫 Partner left the chat.")
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

    # Settings Conversation Handler
    set_handler = ConversationHandler(
        entry_points=[CommandHandler('set', set_start)],
        states={
            GENDER: [CallbackQueryHandler(gender_choice)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_choice)],
            PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, place_choice)],
            TARGET: [CallbackQueryHandler(target_choice)],
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    application.add_handler(set_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))

    application.run_polling(drop_pending_updates=True)
                              
