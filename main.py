import logging, os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

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

# --- BOT LOGIC ---
TOKEN = '8565226350:AAEX2Om5xNMeuCOEqWNocUOpFGhjBWHFcck'

# Database
user_data = {} # {id: {'age': '20', 'gender': 'M', 'target': 'F', 'place': 'Delhi'}}
searching_users = []
active_chats = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['/search', '/set'], ['/stop']]
    await update.message.reply_text(
        "👋 Welcome! Pehle /set se apni profile banayein.\n\n"
        "Example: `/set 22 M Delhi F` (Age Gender Place TargetGender)",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def set_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        # User input: /set 22 M Delhi F
        args = context.args
        if len(args) < 4:
            await update.message.reply_text("❌ Galat format! Aise likhein:\n`/set 22 M Delhi F` \n(Yahan F ka matlab hai aapko Female se baat karni hai)")
            return
        
        user_data[user_id] = {
            'age': args[0],
            'gender': args[1].upper(),
            'place': args[2],
            'target': args[3].upper()
        }
        await update.message.reply_text(f"✅ Profile Saved!\nAge: {args[0]}\nGender: {args[1]}\nPlace: {args[2]}\nTarget: {args[3]}\n\nAb /search karein!")
    except Exception:
        await update.message.reply_text("❌ Kuch galti hui. Check karein.")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id in active_chats:
        await update.message.reply_text("❌ Aap pehle se chat mein hain. /stop karein.")
        return
    
    if user_id not in user_data:
        await update.message.reply_text("⚠️ Pehle profile set karein: `/set 22 M Delhi F`")
        return

    my_pref = user_data[user_id]

    # Perfect Match dhundna
    for partner_id in searching_users:
        partner_pref = user_data.get(partner_id)
        
        # Gender Match Logic: Dono ki pasand ek dusre se milni chahiye
        if partner_pref and partner_pref['gender'] == my_pref['target'] and my_pref['gender'] == partner_pref['target']:
            searching_users.remove(partner_id)
            active_chats[user_id] = partner_id
            active_chats[partner_id] = user_id
            
            await context.bot.send_message(chat_id=user_id, text=f"✅ Match Mila!\nAge: {partner_pref['age']}\nFrom: {partner_pref['place']}\nSay Hello!")
            await context.bot.send_message(chat_id=partner_id, text=f"✅ Match Mila!\nAge: {my_pref['age']}\nFrom: {my_pref['place']}\nSay Hello!")
            return

    if user_id not in searching_users:
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Aapke liye perfect match dhoonda ja raha hai...")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        p_id = active_chats.pop(user_id)
        active_chats.pop(p_id, None)
        await update.message.reply_text("🚫 Chat khatam.")
        await context.bot.send_message(chat_id=p_id, text="🚫 Partner ne chat khatam kar di.")
    elif user_id in searching_users:
        searching_users.remove(user_id)
        await update.message.reply_text("Stopped searching.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_chats:
        await context.bot.send_message(chat_id=active_chats[user_id], text=update.message.text)

if __name__ == '__main__':
    keep_alive()
    app_bot = ApplicationBuilder().token(TOKEN).build()
    
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("set", set_profile))
    app_bot.add_handler(CommandHandler("search", search))
    app_bot.add_handler(CommandHandler("stop", stop))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    
    print("Bot starting with filters...")
    app_bot.run_polling(drop_pending_updates=True)
    
