import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# 1. Replace with your actual Bot Token from BotFather
TOKEN = '8565226350:AAF97KTjahHDUuh89N9wmedklyWUflRD6UQ'

# Dictionary to track searching users and active pairs
searching_users = []
active_chats = {} # {user_id: partner_id}

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
        # Match found!
        partner_id = searching_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        
        await context.bot.send_message(chat_id=user_id, text="✅ Partner found! Say hello.")
        await context.bot.send_message(chat_id=partner_id, text="✅ Partner found! Say hello.")
    else:
        # No one searching, add to list
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
        # Forward text messages to partner
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("❌ You are not connected. Click /search to find someone.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    
    print("Bot is running...")
    app.run_polling()
