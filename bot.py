import logging
import sqlite3
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes



# FEEDBACK MODULINI IMPORT QILISH - TO'G'RILANGAN
from feedback import (
  init_feedback_database, show_feedback_menu, show_surveys, show_admin_chat, 
  show_public_chat, save_survey_answer, save_admin_message, save_public_message,
  delete_public_message, admin_delete_message, get_feedback_stats,
  show_my_admin_messages # YANGI QO'SHILDI
)


# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# Bot sozlamalari
BOT_TOKEN = "7678814266:AAH1XOCV5eE6yr7rwWchtLd6ESrzBrJ447E"
ADMIN_ID = 8069248183
AUTHOR_NAME = "Anonim"


# Hikoya turlari
STORY_TYPES = [
  "💝 Sevgi haqida",
  "🌟 Hayotiy hikoyalar",   
  "🤔 Falsafiy fikrlar",
  "😊 Kulgili voqealar",
  "🎭 Dramatik hikoyalar"
]


# YANGI: Foydalanuvchi holatlari
user_states = {}


# Ma'lumotlar bazasi funksiyalari (eski kodlar)
def init_database():
  conn = sqlite3.connect('hikoyalar.db')
  cursor = conn.cursor()
  
  cursor.execute('''
    CREATE TABLE IF NOT EXISTS stories (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      hikoya_nomi TEXT NOT NULL,
      yozuvchi TEXT NOT NULL,
      tur TEXT NOT NULL,
      tavsif TEXT,
      matn_fayl TEXT,
      audio_fayl TEXT,
      rasm_fayl TEXT,
      sana TEXT
    )
  ''')
  
  conn.commit()
  conn.close()


def add_story(hikoya_nomi, tur, tavsif, matn_fayl=None, audio_fayl=None, rasm_fayl=None):
  conn = sqlite3.connect('hikoyalar.db')
  cursor = conn.cursor()
  
  from datetime import datetime
  sana = datetime.now().strftime("%Y-%m-%d")
  
  cursor.execute('''
    INSERT INTO stories (hikoya_nomi, yozuvchi, tur, tavsif, matn_fayl, audio_fayl, rasm_fayl, sana)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  ''', (hikoya_nomi, AUTHOR_NAME, tur, tavsif, matn_fayl, audio_fayl, rasm_fayl, sana))
  
  conn.commit()
  conn.close()


def get_stories_by_type(tur):
  conn = sqlite3.connect('hikoyalar.db')
  cursor = conn.cursor()
  
  cursor.execute('SELECT * FROM stories WHERE tur = ? ORDER BY id DESC', (tur,))
  stories = cursor.fetchall()
  
  conn.close()
  return stories


def get_story_by_id(story_id):
  conn = sqlite3.connect('hikoyalar.db')
  cursor = conn.cursor()
  
  cursor.execute('SELECT * FROM stories WHERE id = ?', (story_id,))
  story = cursor.fetchone()
  
  conn.close()
  return story


def add_sample_stories():
  sample_stories = [
    ("Bahor kuni", "💝 Sevgi haqida", 
    "Birinchi sevgi haqida hikoya", "bahor.txt", "bahor.mp3", "bahor.jpg"),
    ("Ona duosi", "🌟 Hayotiy hikoyalar", 
    "Onaning farzandiga duosi", "ona.txt", "ona.mp3", "ona.jpg"),
    ("Hayotning ma'nosi", "🤔 Falsafiy fikrlar", 
    "Insonning hayotdagi maqsadi", "maqsad.txt", "maqsad.mp3", "maqsad.jpg"),
    ("Kulgili voqea", "😊 Kulgili voqealar", 
    "Bolaligimdagi qiziq holat", "kulgi.txt", "kulgi.mp3", "kulgi.jpg"),
    ("Ajraliq", "🎭 Dramatik hikoyalar", 
    "Qiyin tanlov haqida", "ajraliq.txt", "ajraliq.mp3", "ajraliq.jpg"),
  ]
  
  for story in sample_stories:
    add_story(*story)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        user_stats = get_user_count()  # Yangi qo'shilgan
        
        keyboard = [
            [InlineKeyboardButton("📚 Hikoyalarim", callback_data="stories")],
            [InlineKeyboardButton("🎧 Audiolar", callback_data="audios")],
            [InlineKeyboardButton("💭 Fikringizni bering", callback_data="feedback_menu")],
            [InlineKeyboardButton("✍️ Men haqimda", callback_data="about")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📖 **HIKOYALAR VA AUDIOLAR**\n\n"
            f"✍️ **Muallif:** {AUTHOR_NAME}\n"
            f"👥 **Foydalanuvchilar:** {user_stats['total_users']} ta\n"  # Yangi qator
            f"🎯 Mening yozgan hikoyalarim va audio versiyalari\n"
            f"🎧 Professional ovozda o'qilgan\n"
            f"📝 Yangi hikoyalar har hafta\n"
            f"💭 Fikrlaringizni ham bildiring!\n\n"
            f"👇 Tanlang:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# YANGILANGAN BUTTON HANDLER
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_chat.type != 'private':
    return
  
  query = update.callback_query
  await query.answer()
  
  # ESKI FUNKSIYALAR
  if query.data == "stories":
    await show_story_types(query)
  elif query.data == "audios":
    await show_audio_stories(query)
  elif query.data == "about":
    await show_about(query)
  elif query.data.startswith("type_"):
    story_type = query.data.replace("type_", "")
    await show_stories_by_type(query, story_type)
  elif query.data.startswith("story_"):
    story_id = query.data.replace("story_", "")
    await show_story_details(query, story_id)
  elif query.data.startswith("read_"):
    story_id = query.data.replace("read_", "")
    await read_story(query, story_id)
  elif query.data.startswith("listen_"):
    story_id = query.data.replace("listen_", "")
    await listen_audio(query, story_id)
  elif query.data == "back_to_types":
    await show_story_types(query)
  elif query.data == "back_to_main":
    await back_to_main(query)
  
  # YANGI FEEDBACK FUNKSIYALAR
  elif query.data == "feedback_menu":
    await show_feedback_menu(query)
  elif query.data == "surveys":
    await show_surveys(query)
  elif query.data == "admin_chat":
    await show_admin_chat(query)
  elif query.data == "public_chat":
    await show_public_chat(query)
  
  # SO'ROVNOMA JAVOBLARI
  elif query.data.startswith("survey_"):
    await handle_survey_start(query)
  
  # XABAR YOZISH
  elif query.data == "write_to_admin":
    await start_admin_message(query)
  elif query.data == "write_public":
    await start_public_message(query)
  
  # XABAR O'CHIRISH
  elif query.data.startswith("delete_msg_"):
    await handle_delete_message(query)


    # BUTTON_HANDLER ga qo'shimcha (mavjud koddan keyin qo'shing)
  
  # YANGI HANDLERLAR
  elif query.data == "my_admin_messages":
    from feedback import show_my_admin_messages # Import qo'shamiz
    await show_my_admin_messages(query)



# YANGI FUNKSIYALAR
async def handle_survey_start(query):
  survey_type = query.data.replace("survey_", "")
  user_id = query.from_user.id
  
  # Foydalanuvchi holatini saqlash
  user_states[user_id] = f"survey_{survey_type}"
  
  questions = {
    "favorite": "❤️ **Qaysi hikoya eng yoqdi?**\n\nHikoya nomini yozing:",
    "topic": "📚 **Qanday mavzuda hikoya yozishimni xohlaysiz?**\n\nMavzuni yozing:",
    "audio": "🎧 **Audio sifati qanday?**\n\nFikringizni yozing:",
    "free": "✍️ **Erkin fikr yozish**\n\nIstalgan fikringizni yozing:"
  }
  
  keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="surveys")]]
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    questions.get(survey_type, "Savol topilmadi"),
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


async def start_admin_message(query):
  user_id = query.from_user.id
  user_states[user_id] = "admin_message"
  
  keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_chat")]]
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    "💬 **ADMIN BILAN GAPLASHISH**\n\n"
    "Xabaringizni yozing. Men tez orada javob beraman:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


async def start_public_message(query):
  user_id = query.from_user.id
  user_states[user_id] = "public_message"
  
  keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="public_chat")]]
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    "👥 **UMUMIY CHAT**\n\n"
    "Xabaringizni yozing. Barcha o'quvchilar ko'radi:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


# MATN XABARLARINI QAYTA ISHLASH
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_chat.type != 'private':
    return
  
  user_id = update.effective_user.id
  user_state = user_states.get(user_id)
  
  if not user_state:
    return
  
  username = update.effective_user.username
  first_name = update.effective_user.first_name
  message_text = update.message.text
  
  # SO'ROVNOMA JAVOBLARI
  if user_state.startswith("survey_"):
    survey_type = user_state.replace("survey_", "")
    
    # Javobni saqlash
    save_survey_answer(user_id, username, first_name, survey_type, message_text)
    
    # Adminга xabar yuborish
    await context.bot.send_message(
      ADMIN_ID,
      f"📝 **YANGI SO'ROVNOMA JAVOBI**\n\n"
      f"👤 **Foydalanuvchi:** {first_name or username or 'Anonim'}\n"
      f"❓ **Savol:** {survey_type}\n"
      f"💬 **Javob:** {message_text}",
      parse_mode='Markdown'
    )
    
    # Foydalanuvchiga tasdiqlash
    keyboard = [[InlineKeyboardButton("📝 Boshqa savol", callback_data="surveys")],
         [InlineKeyboardButton("🔙 Bosh sahifa", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
      "✅ **Javobingiz qabul qilindi!**\n\n"
      "Fikringiz uchun rahmat! 🙏",
      reply_markup=reply_markup,
      parse_mode='Markdown'
    )
  
  # ADMIN BILAN CHAT
  elif user_state == "admin_message":
    # Xabarni saqlash
    save_admin_message(user_id, username, first_name, message_text)
    
    # Adminга yuborish
    await context.bot.send_message(
      ADMIN_ID,
      f"💬 **YANGI XABAR**\n\n"
      f"👤 **Kimdan:** {first_name or username or 'Anonim'}\n"
      f"🆔 **ID:** {user_id}\n"
      f"💌 **Xabar:** {message_text}\n\n"
      f"Javob berish uchun: `/reply {user_id} Javob matni`",
      parse_mode='Markdown'
    )
    
    keyboard = [[InlineKeyboardButton("💬 Yana yozish", callback_data="write_to_admin")],
         [InlineKeyboardButton("🔙 Orqaga", callback_data="feedback_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
      "✅ **Xabaringiz yuborildi!**\n\n"
      "Tez orada javob beraman! 📩",
      reply_markup=reply_markup,
      parse_mode='Markdown'
    )
  
# MATN XABARLARINI QAYTA ISHLASH - TO'G'RILANGAN
async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_chat.type != 'private':
    return
  
  user_id = update.effective_user.id
  user_state = user_states.get(user_id)
  
  if not user_state:
    return
  
  username = update.effective_user.username
  first_name = update.effective_user.first_name
  message_text = update.message.text
  
  # SO'ROVNOMA JAVOBLARI
  if user_state.startswith("survey_"):
    survey_type = user_state.replace("survey_", "")
    
    # Javobni saqlash
    save_survey_answer(user_id, username, first_name, survey_type, message_text)
    
    # Adminга xabar yuborish
    await context.bot.send_message(
      ADMIN_ID,
      f"📝 **YANGI SO'ROVNOMA JAVOBI**\n\n"
      f"👤 **Foydalanuvchi:** {first_name or username or 'Anonim'}\n"
      f"❓ **Savol:** {survey_type}\n"
      f"💬 **Javob:** {message_text}",
      parse_mode='Markdown'
    )
    
    # Foydalanuvchiga tasdiqlash
    keyboard = [[InlineKeyboardButton("📝 Boshqa savol", callback_data="surveys")],
         [InlineKeyboardButton("🔙 Bosh sahifa", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
      "✅ **Javobingiz qabul qilindi!**\n\n"
      "Fikringiz uchun rahmat! 🙏",
      reply_markup=reply_markup,
      parse_mode='Markdown'
    )
  
  # ADMIN BILAN CHAT
  elif user_state == "admin_message":
    # Xabarni saqlash
    save_admin_message(user_id, username, first_name, message_text)
    
    # Adminга yuborish
    await context.bot.send_message(
      ADMIN_ID,
      f"💬 **YANGI XABAR**\n\n"
      f"👤 **Kimdan:** {first_name or username or 'Anonim'}\n"
      f"🆔 **ID:** {user_id}\n"
      f"💌 **Xabar:** {message_text}\n\n"
      f"Javob berish uchun: `/reply {user_id} Javob matni`",
      parse_mode='Markdown'
    )
    
    keyboard = [[InlineKeyboardButton("💬 Yana yozish", callback_data="write_to_admin")],
         [InlineKeyboardButton("🔙 Orqaga", callback_data="feedback_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
      "✅ **Xabaringiz yuborildi!**\n\n"
      "Tez orada javob beraman! 📩",
      reply_markup=reply_markup,
      parse_mode='Markdown'
    )
  
  # UMUMIY CHAT - TO'G'RILANGAN
  elif user_state == "public_message":
    # Xabarni saqlash
    save_public_message(user_id, username, first_name, message_text)
    
    keyboard = [[InlineKeyboardButton("👥 Chatni ko'rish", callback_data="public_chat")],
         [InlineKeyboardButton("✍️ Yana yozish", callback_data="write_public")],
         [InlineKeyboardButton("🔙 Orqaga", callback_data="feedback_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
      "✅ **Xabaringiz umumiy chatga joylandi!**\n\n"
      "Boshqa o'quvchilar ko'rishi mumkin! 👥",
      reply_markup=reply_markup,
      parse_mode='Markdown'
    )
  
  # Holatni tozalash
  if user_id in user_states:
    del user_states[user_id]


# ADMIN FUNKSIYALARI
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return
  
  if len(context.args) < 2:
    await update.message.reply_text(
      "❌ **Noto'g'ri format!**\n\n"
      "To'g'ri format: `/reply USER_ID Javob matni`",
      parse_mode='Markdown'
    )
    return
  
  try:
    target_user_id = int(context.args[0])
    reply_text = " ".join(context.args[1:])
    
    # Foydalanuvchiga javob yuborish
    await context.bot.send_message(
      target_user_id,
      f"💬 **ADMIN JAVOBI**\n\n"
      f"📩 {reply_text}\n\n"
      f"Yana savol bo'lsa, bemalol yozing! 😊",
      parse_mode='Markdown'
    )
    
    # Adminга tasdiqlash
    await update.message.reply_text(
      f"✅ **Javob yuborildi!**\n\n"
      f"👤 **Kimga:** {target_user_id}\n"
      f"💌 **Javob:** {reply_text}",
      parse_mode='Markdown'
    )
    
    # Admin javobini bazaga saqlash
    save_admin_message(ADMIN_ID, "admin", "Admin", reply_text, is_admin_reply=1)
    
  except ValueError:
    await update.message.reply_text("❌ Noto'g'ri foydalanuvchi ID!")
  except Exception as e:
    await update.message.reply_text(f"❌ Xatolik: {str(e)}")


# ADMIN STATISTIKA
# Yangilangan admin stats funksiyasi
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    stats = get_feedback_stats()
    user_stats = get_user_count()  # Yangi qo'shilgan funksiya
    
    text = "📊 **BOT STATISTIKASI**\n\n"
    
    # Foydalanuvchilar statistikasi
    text += f"👥 **Foydalanuvchilar:** {user_stats['total_users']} ta\n"
    text += f"  • So'rovnomalarda: {user_stats['survey_users']} ta\n"
    text += f"  • Admin bilan chatda: {user_stats['admin_chat_users']} ta\n"
    text += f"  • Umumiy chatda: {user_stats['public_chat_users']} ta\n\n"
    
    # Feedback statistikasi
    text += f"📝 **So'rovnomalar:** {stats['survey_count']} ta\n"
    for question_type, count in stats['survey_by_type']:
        text += f"  • {question_type}: {count} ta\n"
    
    text += f"\n💬 **Admin chat:** {stats['user_messages']} ta xabar\n"
    text += f"👥 **Umumiy chat:** {stats['public_messages']} ta xabar\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ESKI FUNKSIYALAR (o'zgarishsiz)
async def show_story_types(query):
  keyboard = []
  for story_type in STORY_TYPES:
    callback_data = f"type_{story_type}"
    keyboard.append([InlineKeyboardButton(story_type, callback_data=callback_data)])
  
  keyboard.append([InlineKeyboardButton("🔙 Bosh sahifa", callback_data="back_to_main")])
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    "📚 **HIKOYA TURLARI**\n\n"
    "Qaysi turdagi hikoyalarni o'qishni xohlaysiz?\n\n"
    "👇 Tanlang:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


async def show_audio_stories(query):
  keyboard = []
  for story_type in STORY_TYPES:
    callback_data = f"type_{story_type}"
    keyboard.append([InlineKeyboardButton(f"🎧 {story_type}", callback_data=callback_data)])
  
  keyboard.append([InlineKeyboardButton("🔙 Bosh sahifa", callback_data="back_to_main")])
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    "🎧 **AUDIO HIKOYALAR**\n\n"
    "Qaysi turdagi audio hikoyalarni tinglashni xohlaysiz?\n\n"
    "👇 Tanlang:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


async def show_about(query):
  keyboard = [[InlineKeyboardButton("🔙 Bosh sahifa", callback_data="back_to_main")]]
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    f"✍️ **MUALLIF HAQIDA**\n\n"
    f"👋 Salom! Men {AUTHOR_NAME}\n\n"
    f"📝 **Nima qilaman:**\n"
    f"• Qiziqarli hikoyalar yozaman\n"
    f"• Ularni audio formatda tayyorlayman\n"
    f"• Har hafta yangi kontent qo'shaman\n\n"
    f"🎯 **Maqsadim:**\n"
    f"• Odamlarni ilhomlantirish\n"
    f"• Foydali vaqt o'tkazishga yordam berish\n"
    f"• O'zbek tilida sifatli kontent yaratish\n\n"
    f"💬 **Aloqa:**\n"
    f"Fikr va takliflaringizni kutaman!\n"
    f"Botdagi 'Fikringizni bering' bo'limidan yozing.",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


async def show_stories_by_type(query, story_type):
  stories = get_stories_by_type(story_type)
  
  if not stories:
    keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_types")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
      f"📭 **{story_type}**\n\n"
      f"Hozircha bu turda hikoyalar yo'q.\n"
      f"Tez orada qo'shiladi! 🔄",
      reply_markup=reply_markup,
      parse_mode='Markdown'
    )
    return
  
  keyboard = []
  for story in stories:
    story_id, hikoya_nomi, _, _, tavsif, _, _, _, sana = story
    keyboard.append([InlineKeyboardButton(f"📖 {hikoya_nomi}", callback_data=f"story_{story_id}")])
  
  keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_types")])
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    f"📚 **{story_type}**\n\n"
    f"Mavjud hikoyalar: {len(stories)} ta\n\n"
    f"👇 Tanlang:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


async def show_story_details(query, story_id):
  story = get_story_by_id(story_id)
  
  if not story:
    await query.answer("❌ Hikoya topilmadi!")
    return
  
  story_id, hikoya_nomi, yozuvchi, tur, tavsif, matn_fayl, audio_fayl, rasm_fayl, sana = story
  
  keyboard = []
  if matn_fayl:
    keyboard.append([InlineKeyboardButton("📖 O'qish", callback_data=f"read_{story_id}")])
  if audio_fayl:
    keyboard.append([InlineKeyboardButton("🎧 Tinglash", callback_data=f"listen_{story_id}")])
  
  keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data=f"type_{tur}")])
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    f"📖 **{hikoya_nomi}**\n\n"
    f"✍️ **Muallif:** {yozuvchi}\n"
    f"📂 **Turi:** {tur}\n"
    f"📅 **Sana:** {sana}\n\n"
    f"📝 **Tavsif:**\n{tavsif}\n\n"
    f"👇 Tanlang:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )


async def read_story(query, story_id):
  story = get_story_by_id(story_id)
  
  if not story or not story[5]: # matn_fayl yo'q
    await query.answer("❌ Matn fayli topilmadi!")
    return
  
  hikoya_nomi = story[1]
  matn_fayl = story[5]
  
  # Fayl mavjudligini tekshirish
  if os.path.exists(matn_fayl):
    try:
      with open(matn_fayl, 'r', encoding='utf-8') as f:
        content = f.read()
      
      keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data=f"story_{story_id}")]]
      reply_markup = InlineKeyboardMarkup(keyboard)
      
      # Matn uzun bo'lsa, qisqartirish
      if len(content) > 3000:
        content = content[:3000] + "...\n\n📖 To'liq matnni fayl sifatida yuklang."
      
      await query.edit_message_text(
        f"📖 **{hikoya_nomi}**\n\n{content}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
      )
    except Exception as e:
      await query.answer(f"❌ Faylni o'qishda xatolik: {str(e)}")
  else:
    await query.answer("❌ Fayl topilmadi!")


async def listen_audio(query, story_id):
  story = get_story_by_id(story_id)
  
  if not story or not story[6]: # audio_fayl yo'q
    await query.answer("❌ Audio fayl topilmadi!")
    return
  
  hikoya_nomi = story[1]
  audio_fayl = story[6]
  
  if os.path.exists(audio_fayl):
    try:
      await query.message.reply_audio(
        audio=open(audio_fayl, 'rb'),
        title=hikoya_nomi,
        performer=AUTHOR_NAME,
        caption=f"🎧 **{hikoya_nomi}**\n\n🎙️ Ovozda: {AUTHOR_NAME}"
      )
      await query.answer("🎧 Audio yuborildi!")
    except Exception as e:
      await query.answer(f"❌ Audio yuborishda xatolik: {str(e)}")
  else:
    await query.answer("❌ Audio fayl topilmadi!")


async def back_to_main(query):
  keyboard = [
    [InlineKeyboardButton("📚 Hikoyalarim", callback_data="stories")],
    [InlineKeyboardButton("🎧 Audiolar", callback_data="audios")],
    [InlineKeyboardButton("💭 Fikringizni bering", callback_data="feedback_menu")],
    [InlineKeyboardButton("✍️ Men haqimda", callback_data="about")]
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)
  
  await query.edit_message_text(
    f"📖 **HIKOYALAR VA AUDIOLAR**\n\n"
    f"✍️ **Muallif:** {AUTHOR_NAME}\n"
    f"🎯 Mening yozgan hikoyalarim va audio versiyalari\n"
    f"🎧 Professional ovozda o'qilgan\n"
    f"📝 Yangi hikoyalar har hafta\n"
    f"💭 Fikrlaringizni ham bildiring!\n\n"
    f"👇 Tanlang:",
    reply_markup=reply_markup,
    parse_mode='Markdown'
  )

  # Yangi funksiya: Foydalanuvchilar sonini hisoblash
def get_user_count():
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    # Barcha tablalardan unique foydalanuvchilarni hisoblash
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM surveys')
    survey_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM admin_chats WHERE is_admin_reply = 0')
    admin_chat_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM public_chat')
    public_chat_users = cursor.fetchone()[0]
    
    # Unique foydalanuvchilar sonini hisoblash
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) FROM (
            SELECT user_id FROM surveys
            UNION SELECT user_id FROM admin_chats WHERE is_admin_reply = 0
            UNION SELECT user_id FROM public_chat
        )
    ''')
    total_users = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_users': total_users,
        'survey_users': survey_users,
        'admin_chat_users': admin_chat_users,
        'public_chat_users': public_chat_users
    }



# XABAR O'CHIRISH - TO'G'RILANGAN
async def handle_delete_message(query):
  data_parts = query.data.split("_")
  if len(data_parts) < 3:
    await query.answer("❌ Noto'g'ri format!")
    return
  
  message_id = data_parts[2]
  user_id = query.from_user.id
  
  # Import qilish
  from feedback import delete_public_message, show_public_chat
  
  # Foydalanuvchi o'z xabarini o'chirmoqchi
  if delete_public_message(message_id, user_id):
    await query.answer("✅ Xabar o'chirildi!")
    await show_public_chat(query) # Chatni yangilash
  else:
    await query.answer("❌ Xabarni o'chirib bo'lmadi!")



# ASOSIY FUNKSIYA
def main():
  # Ma'lumotlar bazasini ishga tushirish
  init_database()
  init_feedback_database() # YANGI
  
  # Namuna hikoyalarni qo'shish (faqat birinchi marta)
  try:
    add_sample_stories()
  except:
    pass # Agar allaqachon mavjud bo'lsa
  
  # Bot yaratish
  application = Application.builder().token(BOT_TOKEN).build()
  
  # Handlerlar
  application.add_handler(CommandHandler("start", start))
  application.add_handler(CommandHandler("reply", admin_reply)) # YANGI
  application.add_handler(CommandHandler("stats", admin_stats)) # YANGI
  application.add_handler(CallbackQueryHandler(button_handler))
  application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)) # YANGI
  
  # Botni ishga tushirish
  print("🚀 Bot ishga tushdi!")
  application.run_polling()


if __name__ == '__main__':
  main()



