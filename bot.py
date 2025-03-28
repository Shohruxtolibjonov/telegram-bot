from telegram.ext import Application, MessageHandler, CommandHandler, filters
import logging
import json
from functools import lru_cache
from pathlib import Path

# O‘zgaruvchilar
TOKEN = '8002330722:AAEUV9Yh-tzFJvoj-mouMfoVgWM9NOkZivw'
CHANNEL_ID = -2319939526
ADMIN_IDS = {1172284285, 886560541}

# Application obyekti yaratish
application = Application.builder().token(TOKEN).build()

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Kalit so‘zlarni JSON fayldan o‘qish
def load_keywords(file_path='keywords.json'):
    try:
        if not Path(file_path).exists():
            default_keywords = {
                'salom': "Salom! Qanday yordam bera olaman?",
                'assalom': "Salom! Qanday yordam bera olaman?",
                'yordam': "Yordam kerakmi? /help ni sinab ko‘ring yoki savolingizni yozing.",
                'help': "Yordam kerakmi? /help ni sinab ko‘ring yoki savolingizni yozing.",
                'rahmat': "Arzimaydi! Yana savollar bo‘lsa, yozing.",
                'tashakkur': "Arzimaydi! Yana savollar bo‘lsa, yozing.",
                'qalay': "Yaxshi, o‘zingiz qalaysiz?",
                'yaxshimisiz': "Yaxshi, o‘zingiz qalaysiz?",
                'nima': "Nima haqida gaplashamiz?",
                'qanday': "Nima haqida gaplashamiz?",
                'xayr': "Xayr! Salomat bo‘ling, yana uchrashguncha.",
                'salomat': "Xayr! Salomat bo‘ling, yana uchrashguncha.",
                'qachon': "Qachon haqida bilmoqchisiz? Aniqlik kiritib yozing.",
                'vaqt': "Qachon haqida bilmoqchisiz? Aniqlik kiritib yozing.",
                'qayerda': "Qayerda ekanligimni bilmoqchimisiz? Men virtual botman!",
                'joy': "Qayerda ekanligimni bilmoqchimisiz? Men virtual botman!",
                'isming': "Mening ismim bot, xizmatingizdaman!",
                'kim': "Mening ismim bot, xizmatingizdaman!",
                'bor': "Ha, men shu yerdaman, siz uchun!",
                'mavjud': "Ha, men shu yerdaman, siz uchun!",
                'yoʻq': "Yo‘qmi? Balki boshqa savol bilan yordam bera olaman.",
                'emas': "Yo‘qmi? Balki boshqa savol bilan yordam bera olaman.",
                'ha': "Zo‘r! Yana nima bilmoqchisiz?",
                'xa': "Zo‘r! Yana nima bilmoqchisiz?",
                'muammo': "Muammo bormi? Tafsilotlarni yozing, yordam beraman.",
                'xato': "Muammo bormi? Tafsilotlarni yozing, yordam beraman.",
                'narx': "Narx haqida ma’lumot kerakmi? Admin bilan bog‘laning.",
                'pul': "Narx haqida ma’lumot kerakmi? Admin bilan bog‘laning.",
                'hozir': "Hozir shu yerda, bugun siz uchun ishlayapman!",
                'bugun': "Hozir shu yerda, bugun siz uchun ishlayapman!"
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_keywords, f, ensure_ascii=False, indent=4)
            return default_keywords
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Kalit so‘zlarni yuklashda xato: {e}")
        return {}

KEYWORDS = load_keywords()

# Chat turini aniqlash uchun yordamchi funksiya (caching bilan)
@lru_cache(maxsize=1000)
def is_valid_chat(chat_type, chat_id, text, bot_username, has_reply):
    text = text.lower() if text else ""
    return (
        chat_type == 'private' or
        (chat_type in ('group', 'supergroup') and f"@{bot_username}" in text) or
        (chat_id == CHANNEL_ID and has_reply)
    )

# Xatoliklarni boshqarish uchun dekorator
def error_handler(func):
    async def wrapper(update, context):
        try:
            return await func(update, context)
        except Exception as e:
            logger.error(f"Xato yuz berdi: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Xatolik yuz berdi, keyinroq urinib ko‘ring."
            )
    return wrapper

# Matnli xabarlarga javob berish
@error_handler
async def handle_text(update, context):
    chat = update.effective_chat
    text = update.message.text
    bot_username = context.bot.username.lower()
    
    if not is_valid_chat(chat.type, chat.id, text, bot_username, update.message.reply_to_message is not None):
        return

    text = text.lower()
    chat_id = chat.id
    user_id = update.effective_user.id

    # Kalit so‘zlarni tekshirish
    responses = [response for keyword, response in KEYWORDS.items() if keyword in text]
    
    if responses:
        await context.bot.send_message(chat_id=chat_id, text="\n".join(responses))
    elif chat.type == 'private' and user_id in ADMIN_IDS:
        await context.bot.send_message(chat_id=chat_id, text="Siz adminsiz!")
    elif chat.type in ('group', 'supergroup', 'channel'):
        await context.bot.send_message(chat_id=chat_id, text="Salom! Admin sizning xabaringizni ko‘rib chiqadi.")

# Rasm yoki videoga javob berish
@error_handler
async def handle_media(update, context):
    chat = update.effective_chat
    text = update.message.text or ""
    bot_username = context.bot.username.lower()
    
    if not is_valid_chat(chat.type, chat.id, text, bot_username, update.message.reply_to_message is not None):
        return
    await context.bot.send_message(
        chat_id=chat.id,
        text="Media uchun rahmat! Yana nima yuborasiz?"
    )

# Start buyrug‘i
@error_handler
async def start(update, context):
    chat = update.effective_chat
    chat_id = chat.id
    chat_type = chat.type
    
    if chat_type == 'private':
        text = "Xush kelibsiz! Botdan foydalanish uchun /help ni bosing."
    elif chat_type in ('group', 'supergroup'):
        text = "Iltimos, /start buyrug‘ini shaxsiy chatda ishlating."
    else:
        return
    await context.bot.send_message(chat_id=chat_id, text=text)

# Handlerlarni qo‘shish
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, handle_media))

# Botni ishga tushirish
if __name__ == '__main__':
    logger.info("Bot ishga tushdi...")
    application.run_polling()