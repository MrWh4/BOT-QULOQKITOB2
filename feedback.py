import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Ma'lumotlar bazasi funksiyalari
def init_feedback_database():
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    # So'rovnoma jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            question_type TEXT NOT NULL,
            answer TEXT NOT NULL,
            sana TEXT NOT NULL
        )
    ''')
    
    # Admin bilan chat jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            message TEXT NOT NULL,
            is_admin_reply INTEGER DEFAULT 0,
            sana TEXT NOT NULL
        )
    ''')
    
    # Umumiy chat jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS public_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            message TEXT NOT NULL,
            sana TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# So'rovnoma funksiyalari
async def show_feedback_menu(query):
    keyboard = [
        [InlineKeyboardButton("📝 So'rovnomalar", callback_data="surveys")],
        [InlineKeyboardButton("💬 Admin bilan gaplashish", callback_data="admin_chat")],
        [InlineKeyboardButton("👥 Umumiy chat", callback_data="public_chat")],
        [InlineKeyboardButton("🔙 Bosh sahifa", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💭 **FIKRINGIZNI BERING**\n\n"
        "📝 So'rovnomalarda qatnashing\n"
        "💬 Men bilan to'g'ridan-to'g'ri gaplashing\n"
        "👥 Boshqa o'quvchilar bilan fikr almashing\n\n"
        "👇 Tanlang:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_surveys(query):
    keyboard = [
        [InlineKeyboardButton("❤️ Qaysi hikoya eng yoqdi?", callback_data="survey_favorite")],
        [InlineKeyboardButton("📚 Qanday mavzuda hikoya yozishimni xohlaysiz?", callback_data="survey_topic")],
        [InlineKeyboardButton("🎧 Audio sifati qanday?", callback_data="survey_audio")],
        [InlineKeyboardButton("✍️ Erkin fikr yozish", callback_data="survey_free")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="feedback_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📝 **SO'ROVNOMALAR**\n\n"
        "Fikringiz men uchun juda muhim!\n"
        "Qaysi savolga javob berishni xohlaysiz?\n\n"
        "👇 Tanlang:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# So'rovnoma javoblarini saqlash
def save_survey_answer(user_id, username, first_name, question_type, answer):
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    sana = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    cursor.execute('''
        INSERT INTO surveys (user_id, username, first_name, question_type, answer, sana)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, question_type, answer, sana))
    
    conn.commit()
    conn.close()

# Admin bilan chat
async def show_admin_chat(query):
    keyboard = [
        [InlineKeyboardButton("✍️ Xabar yozish", callback_data="write_to_admin")],
        [InlineKeyboardButton("📜 Mening xabarlarim", callback_data="my_admin_messages")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="feedback_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💬 **ADMIN BILAN GAPLASHISH**\n\n"
        "Bu yerda men bilan to'g'ridan-to'g'ri gaplashishingiz mumkin.\n"
        "Savollaringiz, takliflaringiz yoki shikoyatlaringizni yozing.\n\n"
        "👇 Tanlang:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# YANGILANGAN - Umumiy chat (xabar o'chirish tugmalari bilan)
async def show_public_chat(query):
    user_id = query.from_user.id
    
    # So'nggi 10 ta xabarni olish
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, username, first_name, message, sana, id 
        FROM public_chat 
        ORDER BY id DESC LIMIT 10
    ''')
    messages = cursor.fetchall()
    conn.close()
    
    text = "👥 **UMUMIY CHAT**\n\n"
    keyboard = []
    
    if messages:
        for msg in reversed(messages):  # Eski xabarlar yuqorida
            msg_user_id, username, first_name, message, sana, msg_id = msg
            name = first_name or username or "Anonim"
            
            # Xabar matni
            text += f"👤 **{name}:** {message}\n"
            text += f"🕐 {sana}\n"
            
            # Agar o'z xabari bo'lsa, o'chirish tugmasini qo'shish
            if msg_user_id == user_id:
                text += f"[🗑️ O'chirish](/delete_msg_{msg_id})\n"
            
            text += "\n"
    else:
        text += "📭 Hozircha xabarlar yo'q.\n"
        text += "Birinchi bo'lib yozing!\n\n"
    
    # Asosiy tugmalar
    keyboard = [
        [InlineKeyboardButton("✍️ Xabar yozish", callback_data="write_public")],
        [InlineKeyboardButton("🔄 Yangilash", callback_data="public_chat")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="feedback_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# YANGI - Foydalanuvchining admin xabarlarini ko'rsatish
async def show_my_admin_messages(query):
    user_id = query.from_user.id
    
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT message, is_admin_reply, sana 
        FROM admin_chats 
        WHERE user_id = ? OR (is_admin_reply = 1 AND user_id = ?)
        ORDER BY id DESC LIMIT 10
    ''', (user_id, user_id))
    messages = cursor.fetchall()
    conn.close()
    
    text = "📜 **MENING XABARLARIM**\n\n"
    
    if messages:
        for message, is_admin_reply, sana in messages:
            if is_admin_reply:
                text += f"🤖 **Admin:** {message}\n"
            else:
                text += f"👤 **Siz:** {message}\n"
            text += f"🕐 {sana}\n\n"
    else:
        text += "📭 Hozircha xabarlar yo'q.\n\n"
    
    keyboard = [
        [InlineKeyboardButton("✍️ Yangi xabar", callback_data="write_to_admin")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="admin_chat")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Xabar saqlash funksiyalari
def save_admin_message(user_id, username, first_name, message, is_admin_reply=0):
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    sana = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    cursor.execute('''
        INSERT INTO admin_chats (user_id, username, first_name, message, is_admin_reply, sana)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, message, is_admin_reply, sana))
    
    conn.commit()
    conn.close()

def save_public_message(user_id, username, first_name, message):
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    sana = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    cursor.execute('''
        INSERT INTO public_chat (user_id, username, first_name, message, sana)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, first_name, message, sana))
    
    conn.commit()
    conn.close()

# Xabar o'chirish
def delete_public_message(message_id, user_id):
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    # Faqat o'z xabarini o'chira oladi
    cursor.execute('DELETE FROM public_chat WHERE id = ? AND user_id = ?', (message_id, user_id))
    
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    return deleted

# Admin uchun xabar o'chirish (har qanday xabar)
def admin_delete_message(message_id, table_name):
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    if table_name == "public_chat":
        cursor.execute('DELETE FROM public_chat WHERE id = ?', (message_id,))
    elif table_name == "admin_chats":
        cursor.execute('DELETE FROM admin_chats WHERE id = ?', (message_id,))
    
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    
    return deleted

# Admin statistika
def get_feedback_stats():
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    # So'rovnoma statistikasi
    cursor.execute('SELECT COUNT(*) FROM surveys')
    survey_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT question_type, COUNT(*) FROM surveys GROUP BY question_type')
    survey_by_type = cursor.fetchall()
    
    # Admin chat statistikasi
    cursor.execute('SELECT COUNT(*) FROM admin_chats WHERE is_admin_reply = 0')
    user_messages = cursor.fetchone()[0]
    
    # Umumiy chat statistikasi
    cursor.execute('SELECT COUNT(*) FROM public_chat')
    public_messages = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'survey_count': survey_count,
        'survey_by_type': survey_by_type,
        'user_messages': user_messages,
        'public_messages': public_messages
    }

# YANGI - Admin uchun barcha feedbacklarni ko'rish
def get_all_surveys():
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT username, first_name, question_type, answer, sana 
        FROM surveys 
        ORDER BY id DESC
    ''')
    surveys = cursor.fetchall()
    
    conn.close()
    return surveys

def get_all_admin_messages():
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT username, first_name, message, is_admin_reply, sana 
        FROM admin_chats 
        ORDER BY id DESC
    ''')
    messages = cursor.fetchall()
    
    conn.close()
    return messages

def get_all_public_messages():
    conn = sqlite3.connect('hikoyalar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT username, first_name, message, sana 
        FROM public_chat 
        ORDER BY id DESC
    ''')
    messages = cursor.fetchall()
    
    conn.close()
    return messages
