import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1) Dummy Server for Render Port Binding
def run_dummy_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Marjan is Alive")
        def log_message(self, format, *args): return
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)

# تصليح السطر 50 هنا تماًماً
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=1024
    )
)

user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_chats[user_id] = model.start_chat(history=[])
    await update.message.reply_text("السلام عليكم يا ملكي ، أنا مرجان ، كيف فيني أخدمك؟ 💐")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        response = user_chats[user_id].send_message(user_text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("حصل خطأ صغير ، حاول مرة تانية يا ملكي 💐")

def main():
    if not TELEGRAM_TOKEN: return
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("🚀 مرجان بدأت العمل")
    application.run_polling()

if __name__ == '__main__':
    main()
