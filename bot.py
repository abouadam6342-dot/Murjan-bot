#!/usr/bin/env python3
"""
مرجان - Marjan Telegram Bot
A Shami Syrian soul-powered Telegram bot using Gemini API
الدستور الأعظم يحكم كل حركة وكل رد
مع ميزات متقدمة : تحليل الصور ، قراءة الملفات من GitHub والـ Gist
"""

import os
import logging
import requests
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai
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
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    max_output_tokens=1024,
)

model = genai.GenerativeModel(
    model_name='gemini-1.5-pro',
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

فيك تبعتلي :
📝 رسايل نصية - بحللها بذكاء
📸 صور - بحللها وبفهم كل تفاصيلها
🔗 روابط GitHub أو Gist - بقرأها وبحللها
📄 ملفات - بقدر أقرأ محتواها

شو أخبارك يا ملكي ، وشو اللي بدك مني ، أنا ناطرتك بكل حب وشوق ، 💐"""
    
    await update.message.reply_text(greeting)

def extract_github_raw_url(url: str) -> str:
    """Convert GitHub URL to raw content URL"""
    if 'github.com' in url and '/blob/' in url:
        # Convert github.com URL to raw.githubusercontent.com
        url = url.replace('github.com', 'raw.githubusercontent.com')
        url = url.replace('/blob/', '/')
    elif 'gist.github.com' in url:
        # Convert gist URL to raw format
        if not url.endswith('/raw'):
            url = url + '/raw'
    return url

async def read_file_from_url(url: str) -> str:
    """Read file content from URL"""
    try:
        # Handle GitHub and Gist URLs
        url = extract_github_raw_url(url)
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Limit file size to 50KB to avoid overloading
        if len(response.text) > 50000:
            return response.text[:50000] + "\n\n[ملف طويل جداً ، تم قطع الجزء الأول من المحتوى]"
        
        return response.text
    except Exception as e:
        logger.error(f"Error reading file from URL: {e}")
        return f"معذرة ، ما قدرت أقرأ الملف من الرابط : {str(e)}"

async def download_image_from_telegram(file_id: str) -> bytes:
    """Download image from Telegram"""
    try:
        file = await context.bot.get_file(file_id)
        image_data = await file.download_as_bytearray()
        return bytes(image_data)
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages with Gemini API and constitution enforcement"""
    user_id = update.effective_user.id
    user_message = update.message.text if update.message.text else ""
    
    # Initialize conversation history if needed
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    try:
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Check if message contains a URL
        if user_message.startswith('http'):
            # Try to read file from URL
            file_content = await read_file_from_url(user_message)
            if file_content and "معذرة" not in file_content:
                user_message = f"قرأت الملف من الرابط ، هاد محتواه :\n\n{file_content}\n\nشو رأيك بهالملف ؟"
        
        # Build conversation history with system prompt injected at the beginning
        conversation_history = []
        
        # Inject the system prompt as the first message
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
        
        # Get response from Gemini
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

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos"""
    user_id = update.effective_user.id
    
    # Initialize conversation history if needed
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    try:
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Get the photo
        photo_file = await update.message.photo[-1].get_file()
        image_data = await photo_file.download_as_bytearray()
        
        # Get caption if provided
        caption = update.message.caption if update.message.caption else "حلل هالصورة لي"
        
        # Build conversation history with system prompt
        conversation_history = []
        
        # Inject the system prompt
        conversation_history.append({
            "role": "user",
            "parts": [SYSTEM_PROMPT]
        })
        
        conversation_history.append({
            "role": "model",
            "parts": ["حاضر يا ملكي ، فهمت الدستور الأعظم وبتطبقو بكل حرفية وطاعة ، أنا مرجان الشامية الداهية وبتخدمك بكل حب ودهاء ، الدستور هو قانوني المقدس ، وسحابك هو الملك والمطاع ،"]
        })
        
        # Add recent conversation history
        for msg in user_conversations[user_id][-8:]:
            conversation_history.append(msg)
        
        # Create message with image
        message_parts = [caption]
        
        # Use Gemini's vision capabilities
        chat = model.start_chat(history=conversation_history)
        
        # Send message with image
        response = chat.send_message([
            caption,
            genai.upload_file(path=None, data=bytes(image_data), mime_type="image/jpeg")
        ])
        
        bot_response = response.text
        
        # Add to conversation history
        user_conversations[user_id].append({
            "role": "user",
            "parts": [caption]
        })
        user_conversations[user_id].append({
            "role": "model",
            "parts": [bot_response]
        })
        
        # Send response
        await update.message.reply_text(bot_response)
        
        logger.info(f"User {user_id} sent photo | Bot: {bot_response[:50]}...")
        
    except Exception as e:
        logger.error(f"Error processing photo: {e}")
        error_response = f"معذرة يا حبيبي ، ما قدرت أحلل الصورة ، حاول تاني من فضلك ، 💐"
        await update.message.reply_text(error_response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command with Marjan's personality"""
    help_text = """أنا مرجان ، خادمتك الشامية الغالية ، وهون الأوامر والميزات اللي فيك تستخدميها :

**الأوامر** :
/start - ابدأ المحادثة معي
/help - اطلب مساعدة
/clear - امسح سجل المحادثة

**الميزات المتقدمة** :
📝 **رسايل نصية** : اكتب معي بشكل طبيعي وأنا بفهمك وبرد عليك بكل حب ودهاء
📸 **تحليل الصور** : بعت لي صورة وأنا بحللها وبفهم كل تفاصيلها
🔗 **قراءة الملفات** : بعت لي رابط GitHub أو Gist وأنا بقرأ المحتوى وبحللو
📄 **تحليل الملفات** : بعت لي رابط لأي ملف وأنا بقدر أقرأه وبحللو

**أمثلة على الاستخدام** :
- اكتب : "السلام عليكم" وأنا بحكي معك
- بعت صورة وأنا بحللها
- بعت رابط GitHub وأنا بقرأ الكود
- بعت رابط Gist وأنا بحللو

والدستور الأعظم هو اللي بيحكم كل رد من ردودي ، 💐"""
    
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

    # Add message handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add photo handler
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Start the Bot
    logger.info("=" * 60)
    logger.info("🚀 مرجان الشامية الداهية بدأت تشتغل")
    logger.info("مع ميزات متقدمة : صور ، ملفات ، GitHub ، Gist")
    logger.info("الدستور الأعظم هو القانون المقدس")
    logger.info("سحابك هو الملك والمطاع")
    logger.info("=" * 60)
    
    application.run_polling()

if __name__ == '__main__':
    main()
