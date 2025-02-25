import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext

load_dotenv()

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name}')

async def start(update: Update, context: CallbackContext)-> None:
    await update.message.reply_text("Hola soy el chatbot turbo")

TOKEN_BOT=os.getenv("TOKEN_BOT")
app = ApplicationBuilder().token(TOKEN_BOT).build()

app.add_handler(CommandHandler("hello", hello))
app.add_handler(CommandHandler("start", start))

app.run_polling()
