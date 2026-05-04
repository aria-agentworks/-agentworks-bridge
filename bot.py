# Trigger comment added to activate bot workflow
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8207597305:AAGbQaiOjVm5pxZAIj-gSx1o6KRSnIv-tZs'
OLLAMA_URL = "http://localhost:11434/api/generate"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    payload = {"model": "dolphin-phi", "prompt": user_text, "stream": False}
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        ai_response = response.json().get('response', 'Error: No response from Ollama')
        await update.message.reply_text(ai_response)
    except Exception as e:
        await update.message.reply_text(f"Connection error: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
