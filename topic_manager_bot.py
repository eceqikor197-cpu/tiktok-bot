import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import json
import datetime

# ==========================================
# --- НАСТРОЙКИ ---
# ==========================================

BOT_TOKEN = os.getenv('BOT_TOKEN', '8979713384:AAHOjZYO7jUJWTr3ggbYsgd4jThWXZXYtRU')

if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА' or not BOT_TOKEN or ':' not in BOT_TOKEN:
    print("❌ Ошибка: Вставьте ваш реальный токен Telegram бота в переменную BOT_TOKEN в файле bot.py или задайте переменную окружения BOT_TOKEN.")
    exit(1)

# Список чатов (Внимание: ID групп-форумов обычно начинаются с -100)
CHATS = {
    "Основная группа": -1004413303837,
    "Тик ток | Рабочий": -1002993185724,
}

# Список имен для создания тем
NAMES = [
    "@qwooassqwp",
    "@llllkkklllll",
    "@saiida_me",
    "@pollinkaa_sfr",
    "@d_r_k23",
    "@pqbdpqbdp",
    "@kpau6a6y"
]

# Список предметов из календаря
SUBJECTS = [
    "Высшая математика (л.)",
    "Высшая математика (пр.)",
    "Иностранный язык (пр.)",
    "Информационные технологии (л.)",
    "Информационные технологии (пр.)",
    "Основы российской государственности (л.)",
    "Основы российской государственности (пр.)",
    "Социальное взаимодействие (л.)",
    "Социальное взаимодействие (пр.)",
    "Статистика (л.)",
    "Статистика (пр.)",
    "Философия (л.)",
    "Философия (пр.)",
    "Экология (л.)",
    "Экология (пр.)",
    "Экономическая грамотность в условиях цифровой трансформации (л.)",
    "Экономическая грамотность в условиях цифровой трансформации (пр.)",
    "Экономическая теория (л.)",
    "Экономическая теория (пр.)"
]

# Файл для хранения ID созданных тем для всех чатов
DATA_FILE = "/Users/danilakonovalov/.gemini/antigravity/scratch/tiktok_bot/last_topics_all.json"

bot = telebot.TeleBot(BOT_TOKEN)

def get_data():
    """Читает базу данных с темами."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_data(data):
    """Сохраняет базу данных."""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def get_last_topics(chat_id, category):
    """Получает старые темы для конкретного чата и категории (names или subjects)."""
    data = get_data()
    return data.get(str(chat_id), {}).get(category, [])

def save_new_topics(chat_id, category, topic_ids):
    """Сохраняет новые темы для чата и категории."""
    data = get_data()
    chat_id_str = str(chat_id)
    if chat_id_str not in data:
        data[chat_id_str] = {}
    data[chat_id_str][category] = topic_ids
    save_data(data)

def delete_old_topics(chat_id, category):
    """Удаляет старые темы в чате."""
    old_topics = get_last_topics(chat_id, category)
    for topic_id in old_topics:
        try:
            bot.delete_forum_topic(chat_id=chat_id, message_thread_id=topic_id)
            print(f"Старая тема (ID: {topic_id}) удалена в чате {chat_id}.")
        except Exception as e:
            print(f"Не удалось удалить тему {topic_id} в чате {chat_id}: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(message):
    """Отправляет ID группы при добавлении бота"""
    bot_info = bot.get_me()
    for member in message.new_chat_members:
        if member.id == bot_info.id:
            print(f"🎉 Бота добавили в группу '{message.chat.title}': ID = {message.chat.id}")
            bot.send_message(message.chat.id, f"👋 Привет! Бот подключен.\n📍 **ID этой группы:** `{message.chat.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['id'])
def handle_id_command(message):
    """Показывает ID текущего чата"""
    chat_title = message.chat.title or "Личный чат"
    print(f"📍 Запрос ID из чата '{chat_title}': {message.chat.id}")
    bot.send_message(message.chat.id, f"📍 **ID текущего чата:** `{message.chat.id}`\nНазвание: **{chat_title}**", parse_mode="Markdown")

@bot.message_handler(func=lambda message: not (message.text and message.text.startswith('/')), content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'contact', 'location', 'venue', 'animation', 'dice', 'poll', 'story'])
def handle_forwarded_message(message):
    """Обрабатывает все сообщения, чтобы найти пересланные и вытащить ID"""
    if message.forward_origin:
        if hasattr(message.forward_origin, 'chat'):
            chat = message.forward_origin.chat
            print(f"🔄 Получено пересланное сообщение из чата '{chat.title}' (ID: {chat.id})")
            bot.send_message(message.chat.id, f"✅ Я увидел пересланное сообщение!\nНазвание: **{chat.title}**\nID: `{chat.id}`", parse_mode="Markdown")
        elif hasattr(message.forward_origin, 'sender_user'):
            user = message.forward_origin.sender_user
            print(f"🔄 Переслано от пользователя {user.first_name} (ID: {user.id})")
        else:
            print(f"🔄 Пересланное сообщение, но ID группы скрыт настройками приватности.")
    else:
        # Не пересланное сообщение
        print(f"💬 Новое сообщение: {message.text or '<не текст>'} от {message.from_user.first_name}")

@bot.message_handler(commands=['menu', 'start'])
def handle_menu_command(message):
    """Отправляет сообщение с выбором чата"""
    markup = InlineKeyboardMarkup()
    
    # Создаем кнопки для каждого чата
    for chat_name, chat_id in CHATS.items():
        btn = InlineKeyboardButton(f"💬 {chat_name}", callback_data=f"chat_{chat_id}")
        markup.add(btn)
        
    bot.send_message(message.chat.id, "Выберите, в какой группе будем создавать темы:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("chat_"))
def handle_chat_selection(call):
    """Обработка выбора чата - показываем, что создавать"""
    chat_id = call.data.split("_")[1]
    
    # Находим название чата по ID для красивого сообщения
    chat_name = "Неизвестный чат"
    for name, cid in CHATS.items():
        if str(cid) == chat_id:
            chat_name = name
            break

    markup = InlineKeyboardMarkup()
    btn_names = InlineKeyboardButton("👥 Создать темы по именам", callback_data=f"askdate_names_{chat_id}")
    btn_subjects = InlineKeyboardButton("📚 Создать темы по предметам", callback_data=f"do_subjects_{chat_id}")
    btn_back = InlineKeyboardButton("⬅️ Назад", callback_data="back_to_chats")
    
    markup.add(btn_names)
    markup.add(btn_subjects)
    markup.add(btn_back)
    
    bot.edit_message_text(f"Группа: **{chat_name}**\nВыберите, какие темы нужно создать:", 
                          chat_id=call.message.chat.id, 
                          message_id=call.message.message_id, 
                          reply_markup=markup, 
                          parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("askdate_"))
def handle_ask_date(call):
    """Меню выбора даты"""
    _, category, chat_id = call.data.split("_")
    markup = InlineKeyboardMarkup()
    
    # Генерируем 5 ближайших дней
    today = datetime.datetime.now()
    for i in range(5):
        d = today + datetime.timedelta(days=i)
        date_str = d.strftime("%d.%m.%Y")
        label = date_str
        if i == 0: label += " (Сегодня)"
        elif i == 1: label += " (Завтра)"
        
        markup.add(InlineKeyboardButton(label, callback_data=f"dodate_{category}_{chat_id}_{date_str}"))
        
    markup.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"chat_{chat_id}"))
    
    bot.edit_message_text("Выберите дату для тем:", 
                          chat_id=call.message.chat.id, 
                          message_id=call.message.message_id, 
                          reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_chats")
def handle_back(call):
    """Возврат к списку чатов"""
    handle_menu_command(call.message)
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("do_") or call.data.startswith("dodate_"))
def handle_creation(call):
    """Обработка нажатий на создание тем"""
    parts = call.data.split("_")
    action = parts[0]
    category = parts[1]
    chat_id = int(parts[2])
    
    date_str = datetime.datetime.now().strftime("%d.%m.%Y")
    if action == "dodate":
        date_str = parts[3]
    
    if category == "names":
        bot.answer_callback_query(call.id, "Создаю темы по именам...")
        bot.edit_message_text(f"⏳ Создаю темы на {date_str}...", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        new_topics_ids = []
        
        last_error = None
        for name in NAMES:
            topic_name = f"{name} {date_str}"
            try:
                new_topic = bot.create_forum_topic(chat_id=chat_id, name=topic_name)
                new_topics_ids.append(new_topic.message_thread_id)
            except Exception as e:
                last_error = e
                print(f"Ошибка создания темы '{topic_name}': {e}")
                
        save_new_topics(chat_id, "names", new_topics_ids)
        if new_topics_ids:
            bot.send_message(call.message.chat.id, f"✅ Темы по именам на {date_str} успешно созданы!\nСоздано: {len(new_topics_ids)}")
        else:
            error_msg = f" (Причина: {last_error})" if last_error else ""
            bot.send_message(call.message.chat.id, f"⚠️ Не удалось создать темы{error_msg}.\n\n👉 **Убедитесь, что бот назначен Администратором в группе и ему включено право «Управление темами» (Manage Topics).**", parse_mode="Markdown")

    elif category == "subjects":
        bot.answer_callback_query(call.id, "Создаю темы по предметам...")
        bot.edit_message_text("⏳ Начинаю обновление тем по предметам...", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
        new_topics_ids = []
        
        last_error = None
        for subject in SUBJECTS:
            try:
                new_topic = bot.create_forum_topic(chat_id=chat_id, name=subject)
                new_topics_ids.append(new_topic.message_thread_id)
            except Exception as e:
                last_error = e
                print(f"Ошибка создания темы '{subject}': {e}")
                
        save_new_topics(chat_id, "subjects", new_topics_ids)
        if new_topics_ids:
            bot.send_message(call.message.chat.id, f"✅ Темы по предметам успешно обновлены в чате!\nСоздано: {len(new_topics_ids)}")
        else:
            error_msg = f" (Причина: {last_error})" if last_error else ""
            bot.send_message(call.message.chat.id, f"⚠️ Не удалось создать темы{error_msg}.\n\n👉 **Убедитесь, что бот назначен Администратором в группе и ему включено право «Управление темами» (Manage Topics).**", parse_mode="Markdown")

if __name__ == '__main__':
    print("🤖 Бот запущен. Напишите /menu для вызова меню...")
    bot.infinity_polling()
