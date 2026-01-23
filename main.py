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
ttt_games = {} 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- TIC-TAC-TOE LOGIC ---
def check_winner(board):
    win_cond = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for c in win_cond:
        if board[c[0]] == board[c[1]] == board[c[2]] != " ":
            return board[c[0]]
    if " " not in board: return "Draw"
    return None

async def start_ttt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    partner_id = active_chats.get(user_id)
    
    if not partner_id:
        await update.message.reply_text("❌ Pehle kisi se connect hon (/search).")
        return
    
    game_id = tuple(sorted((user_id, partner_id)))
    ttt_games[game_id] = {"board": [" "] * 9, "turn": user_id, "X": user_id, "O": partner_id}
    
    # Dono ko board bhejein
    await send_ttt_board(context, user_id, game_id, "🎮 Tic-Tac-Toe shuru! Aapki bari (X)")
    await send_ttt_board(context, partner_id, game_id, "🎮 Partner ne game shuru kiya! Unki bari (X)")

async def send_ttt_board(context, chat_id, game_id, text):
    board = ttt_games[game_id]["board"]
    kb = []
    for i in range(0, 9, 3):
        row = [InlineKeyboardButton(board[i+j] if board[i+j] != " " else "⬜", callback_data=f"ttt_{i+j}") for j in range(3)]
        kb.append(row)
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(kb))

# --- BUTTON CLICK HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("ttt_"):
        partner_id = active_chats.get(user_id)
        if not partner_id: 
            await query.answer("Chat khatam ho chuki hai.")
            return
            
        game_id = tuple(sorted((user_id, partner_id)))
        if game_id not in ttt_games: 
            await query.answer("Game purana ho gaya hai, naya shuru karein.")
            return
            
        game = ttt_games[game_id]
        if game["turn"] != user_id:
            await query.answer("❌ Intezar karein, abhi aapki bari nahi hai!", show_alert=True)
            return
        
        idx = int(data.split("_")[1])
        if game["board"][idx] != " ": 
            await query.answer("Ye jagah pehle se bhari hai!")
            return

        # Move update karein
        symbol = "X" if game["X"] == user_id else "O"
        game["board"][idx] = symbol
        game["turn"] = partner_id
        
        winner = check_winner(game["board"])
        if winner:
            result_msg = f"🏁 Game Over! {'Match Draw! 🤝' if winner == 'Draw' else winner + ' Jeet Gaya! 🎉'}"
            await context.bot.send_message(chat_id=user_id, text=result_msg)
            await context.bot.send_message(chat_id=partner_id, text=result_msg)
            ttt_games.pop(game_id, None)
        else:
            await query.delete_message()
            await send_ttt_board(context, user_id, game_id, "✅ Move saved. Partner ki bari...")
            await send_ttt_board(context, partner_id, game_id, f"👉 Aapki bari! ({'O' if symbol == 'X' else 'X'})")

# --- MAIN COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [['🚀 Find a partner'], ['⚙️ Settings', '🚫 Stop']]
    await update.message.reply_text("👋 Welcome! Chat shuru hone ke baad /game likhein.", 
                                   reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "🚀 Find a partner":
        if user_id in searching_users:
            await update.message.reply_text("⏳ Searching...")
            return
        searching_users.append(user_id)
        await update.message.reply_text("🔎 Partner dhoonda ja raha hai...")
        if len(searching_users) >= 2:
            p1, p2 = searching_users.pop(0), searching_users.pop(0)
            active_chats[p1], active_chats[p2] = p2, p1
            await context.bot.send_message(chat_id=p1, text="✅ Connected! Game ke liye /game likhein.")
            await context.bot.send_message(chat_id=p2, text="✅ Connected! Game ke liye /game likhein.")
            
    elif text == "🚫 Stop":
        if user_id in active_chats:
            p_id = active_chats.pop(user_id)
            active_chats.pop(p_id, None)
            await update.message.reply_text("🚫 Chat ended.")
            await context.bot.send_message(chat_id=p_id, text="🚫 Partner left.")
        elif user_id in searching_users:
            searching_users.remove(user_id)
            await update.message.reply_text("Stopped.")

    elif user_id in active_chats:
        await context.bot.send_message(chat_id=active_chats[user_id], text=text)

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", start_ttt))
    application.add_handler(CallbackQueryHandler(button_handler)) # Buttons ke liye zaroori
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    
    application.run_polling(drop_pending_updates=True)
    
