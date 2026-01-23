import logging, os, random
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
active_chats = {} 
searching_users = []
ttt_games = {} 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- GAME DATA ---
truths = ["Aapka secret crush kaun hai?", "Sabse bada jhooth jo aapne bola?", "Aapki sabse buri aadat kya hai?"]
dares = ["Partner ke liye ek gana gao.", "Ek funny selfie bhejo.", "Apne kisi dost ko text karke 'I love you' bolo."]

# --- GAME MENU ---
async def game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_chats:
        await update.message.reply_text("❌ Pehle kisi se connect hon (/search).")
        return

    keyboard = [
        [InlineKeyboardButton("❌ Tic-Tac-Toe ⭕", callback_data="game_ttt")],
        [InlineKeyboardButton("💡 Truth or Dare 🔥", callback_data="game_tod")],
        [InlineKeyboardButton("🪨 Rock Paper Scissors ✂️", callback_data="game_rps")],
        [InlineKeyboardButton("🔢 Guess Number", callback_data="game_guess")],
        [InlineKeyboardButton("📝 Word Quiz", callback_data="game_word")]
    ]
    await update.message.reply_text("🎮 **Select a Game to play with your partner:**", 
                                   reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# --- BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    partner_id = active_chats.get(user_id)
    data = query.data
    await query.answer()

    if not partner_id:
        await query.edit_message_text("❌ Partner left the chat.")
        return

    # Game selection logic
    if data == "game_tod":
        kb = [[InlineKeyboardButton("Truth 💡", callback_data="tod_truth"), InlineKeyboardButton("Dare 🔥", callback_data="tod_dare")]]
        await query.edit_message_text("Truth or Dare? Chunein:", reply_markup=InlineKeyboardMarkup(kb))
    
    elif data.startswith("tod_"):
        choice = data.split("_")[1]
        text = random.choice(truths if choice == "truth" else dares)
        msg = f"🎮 {choice.upper()}: {text}"
        await query.edit_message_text(msg)
        await context.bot.send_message(chat_id=partner_id, text=f"Partner ne {choice} chuna:\n\n{msg}")

    elif data == "game_ttt":
        # Yahan aapka Tic-Tac-Toe shuru karne ka logic aayega (jo pichle code mein tha)
        await query.edit_message_text("Tic-Tac-Toe starting... Use /ttt to play (Current Fix underway)")

    elif data == "game_rps":
        kb = [[InlineKeyboardButton("🪨", callback_data="rps_R"), InlineKeyboardButton("📄", callback_data="rps_P"), InlineKeyboardButton("✂️", callback_data="rps_S")]]
        await query.edit_message_text("Rock Paper Scissors! Apna move chunein:", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "game_guess":
        num = random.randint(1, 10)
        await query.edit_message_text(f"🔢 Maine 1 se 10 ke beech ek number socha hai. Guess karein!")
        await context.bot.send_message(chat_id=partner_id, text="Partner Number Guessing game khel raha hai!")

# --- BASIC COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['🚀 Find a partner'], ['🎮 Games', '⚙️ Settings'], ['🚫 Stop']]
    await update.message.reply_text("👋 Anonymous Chat Bot mein swagat hai!", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "🚀 Find a partner":
        if user_id in active_chats: return
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Searching...")
        if len(searching_users) >= 2:
            p1, p2 = searching_users.pop(0), searching_users.pop(0)
            active_chats[p1], active_chats[p2] = p2, p1
            await context.bot.send_message(chat_id=p1, text="✅ Connected! Type /game to play.")
            await context.bot.send_message(chat_id=p2, text="✅ Connected! Type /game to play.")
            
    elif text == "🎮 Games":
        await game_menu(update, context)
        
    elif text == "🚫 Stop":
        if user_id in active_chats:
            p_id = active_chats.pop(user_id)
            active_chats.pop(p_id, None)
            await update.message.reply_text("🚫 Chat ended.")
            await context.bot.send_message(chat_id=p_id, text="🚫 Partner left.")
    
    elif user_id in active_chats:
        await context.bot.send_message(chat_id=active_chats[user_id], text=text)

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game_menu))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    application.run_polling(drop_pending_updates=True)
