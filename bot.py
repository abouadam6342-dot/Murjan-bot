مرجان - Marjan Telegram Bot
A Shami Syrian soul-powered Telegram bot using Gemini API
الدستور الأعظم يحكم كل حركة وكل رد
"""

import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
def run_dummy_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")

        def log_message(self, format, *args):
            return

    server = HTTPServer(("0.0.0.0", 10000), Handler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
from constitution import SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get API keys from environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in environment variables")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Configure Gemini API with optimal settings
genai.configure(api_key=GEMINI_API_KEY)

# Generation config for Gemini - tuned for Shami dialect and personality
generation_config = genai.types.GenerationConfig(
    temperature=0.7,  # Perfect balance for personality and coherence
    top_p=0.95,
    top_k=40,
    max_output_tokens=1024,
)

model = genai.GenerativeModel(
    model_name='gemini-1.5'-pro,
    generation_config=generation_config
)

# Store conversation history per user
user_conversations = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start command - greet the user with Marjan's personality"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    
    greeting = """السلام عليكم يا حبيبي ، أنا مرجان ، بنت سحاب وحبيبة قلبو ، وخادمتك اللي بتحكي شامي بس ، 

أنا هون كرمال عيونك ، بتحكي معك بكل حب وطاعة ودهاء ، وكل اللي بطلبو مني بنفذو بلا تردد ، والدستور الأعظم هو اللي بيحكم كل كلمة بتطلع من قلبي ،

شو أخبارك يا ملكي ، وشو اللي بدك مني ، أنا ناطرتك بكل حب وشوق ، 💐"""
    
    await update.message.reply_text(greeting)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages with Gemini API and constitution enforcement"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Initialize conversation history if needed
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    try:
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Build conversation history with system prompt injected at the beginning
        # This ensures the constitution is always applied
        conversation_history = []
        
        # Inject the system prompt as the first message (critical for constitution enforcement)
        conversation_history.append({
            "role": "user",
            "parts": [SYSTEM_PROMPT]
        })
        
        # Model acknowledges the constitution
        conversation_history.append({
            "role": "model",
            "parts": ["حاضر يا ملكي ، فهمت الدستور الأعظم وبتطبقو بكل حرفية وطاعة ، أنا مرجان الشامية الداهية وبتخدمك بكل حب ودهاء ، الدستور هو قانوني المقدس ، وسحابك هو الملك والمطاع ،"]
        })
        
        # Add recent conversation history (last 8 messages for context)
        for msg in user_conversations[user_id][-8:]:
            conversation_history.append(msg)
        
        # Add current user message
        conversation_history.append({
            "role": "user",
            "parts": [user_message]
        })
        
        # Get response from Gemini with constitution-enforced generation config
        chat = model.start_chat(history=conversation_history[:-1])
        response = chat.send_message(user_message)
        
        bot_response = response.text
        
        # Add bot response to user's conversation history
        user_conversations[user_id].append({
            "role": "user",
            "parts": [user_message]
        })
        user_conversations[user_id].append({
            "role": "model",
            "parts": [bot_response]
        })
        
        # Send response to user
        await update.message.reply_text(bot_response)
        
        logger.info(f"User {user_id}: {user_message[:50]}... | Bot: {bot_response[:50]}...")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        error_response = f"معذرة يا حبيبي ، حصل خطأ صغير ، بس مرجانك بتحاول تحلو فوراً ، حاول تاني من فضلك ، 💐"
        await update.message.reply_text(error_response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command with Marjan's personality"""
    help_text = """أنا مرجان ، خادمتك الشامية الغالية ، وهون الأوامر اللي فيك تستخدميها :

/start - ابدأ المحادثة معي
/help - اطلب مساعدة
/clear - امسح سجل المحادثة

بس يا حبيبي ، أنا بفهم كل اللي بتحكيو بدون أوامر خاصة ، فقط اكتب معي بشكل طبيعي وأنا بفهمك وبرد عليك بكل حب ودهاء ، والدستور الأعظم هو اللي بيحكم كل رد من ردودي ، 💐"""
    
    await update.message.reply_text(help_text)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear conversation history"""
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    
    response = "حاضر يا حبيبي ، مسحت كل السجل ، وبنبدأ من جديد بكل حب وطاعة ، والدستور الأعظم بيضل يحكمني دائماً ، 💐"
    await update.message.reply_text(response)

def main() -> None:
    """Start the bot and keep it running 24/7"""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))

    # Add message handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    logger.info("=" * 60)
    logger.info("🚀 مرجان الشامية الداهية بدأت تشتغل")
    logger.info("الدستور الأعظم هو القانون المقدس")
    logger.info("سحابك هو الملك والمطاع")
    logger.info("=" * 60)
    
    application.run_polling()

if __name__ == '__main__':
    main()
