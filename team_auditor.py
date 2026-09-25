import os
import json
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
import imagehash
from PIL import Image
import subprocess

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

SESSION_FILE = 'auditor_session'
DB_FILE = 'hashes_db.json'
DOWNLOAD_DIR = 'auditor_downloads'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Ключевые слова для проверки OCR
SUCCESS_KEYWORDS = [
    "Долго искал", "Тоже долго", "Кстати, для подготовки", "нормальные варианты",
    "сильные преподаватели", "перешел на Яблоко", "спасаюсь через", "много хорошего про",
    "друзья посоветовали", "топовую подготовку", "Никак не мог определиться",
    "адекватное по стоимости", "Часто вижу рекомендации", "реально полезные",
    "Перепробовал кучу", "Яблоко"
]

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def get_text_from_image(image_path):
    script_path = os.path.join(os.path.dirname(__file__), 'ocr.swift')
    try:
        out = subprocess.check_output(['swift', script_path, image_path], text=True)
        return out
    except:
        return ""

async def main():
    print("=== Бот-Аудитор для проверки скриншотов ===")
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    await client.start()
    
    print("\nПодключение успешно! Получаем список ваших чатов...")
    dialogs = await client.get_dialogs(limit=150)
    
    print("\nПоследние 15 чатов:")
    for i in range(min(15, len(dialogs))):
        print(f"[{i}] {dialogs[i].name}")
        
    choice = input("\nВведите номер чата ИЛИ часть его названия (если его нет в списке): ").strip()
    
    chat = None
    if choice.isdigit() and int(choice) < len(dialogs):
        chat = dialogs[int(choice)]
    else:
        # Ищем по названию
        for d in dialogs:
            if choice.lower() in d.name.lower():
                chat = d
                break
                
    if not chat:
        print("Чат не найден. Попробуйте запустить скрипт снова и ввести более точное название.")
        return
        
    print(f"\nВыбран чат: {chat.name}")
    
    # Читаем базу топиков из бота tg_topic_bot
    topics_file = "/Users/danilakonovalov/.gemini/antigravity/scratch/tiktok_bot/last_topics_all.json"
    target_topic_ids = []
    
    if os.path.exists(topics_file):
        try:
            with open(topics_file, 'r', encoding='utf-8') as f:
                topic_data = json.load(f)
                chat_id_str = str(chat.id)
                # Telethon chat IDs for supergroups start with -100, but sometimes chat.id doesn't include it.
                # Let's check both chat_id_str and f"-100{chat.id}"
                possible_keys = [chat_id_str, f"-100{chat.id}"]
                
                chat_topics_data = None
                for k in possible_keys:
                    if k in topic_data:
                        chat_topics_data = topic_data[k]
                        break
                        
                if chat_topics_data:
                    for category, t_ids in chat_topics_data.items():
                        target_topic_ids.extend(t_ids)
        except Exception as e:
            print(f"Ошибка чтения файла топиков: {e}")
            
    if not target_topic_ids:
        print("\nВ last_topics_all.json не найдено активных топиков для этого чата!")
        proceed = input("Проверить ВСЕ топики в чате? (y/n): ").strip().lower()
        if proceed != 'y':
            return
            
    print(f"\nНайдено целевых топиков для проверки: {len(target_topic_ids)}")
    
    topic_mapping = {}
    if getattr(chat, 'forum', False):
        print("Загружаю названия топиков...")
        topics = await client.get_forum_topics(chat)
        for t in topics:
            if not target_topic_ids or t.id in target_topic_ids:
                topic_mapping[t.id] = t.title
    
    days_str = input("\nЗа сколько последних дней проверить скриншоты? [по умолчанию 7]: ").strip()
    days = int(days_str) if days_str.isdigit() else 7
    time_limit = datetime.now(timezone.utc) - timedelta(days=days)
    
    print(f"\nСкачиваем скриншоты за последние {days} дней... (это займет время)")
    
    messages_with_photos = []
    async for message in client.iter_messages(chat, offset_date=time_limit, reverse=False):
        if message.photo:
            topic_id = message.reply_to_msg_id if message.reply_to else None
            
            # Если у нас есть целевые топики, проверяем только их
            if target_topic_ids and topic_id not in target_topic_ids:
                continue
                
            messages_with_photos.append((message, topic_id))
            
    print(f"Найдено скриншотов для проверки: {len(messages_with_photos)}")
    if not messages_with_photos:
        return
        
    db = load_db()
    print("Начинаем проверку (OCR + анти-дубликаты)...")
    
    report = {}
    new_hashes_this_run = {}
    
    for msg, t_id in messages_with_photos:
        topic_name = topic_mapping.get(t_id, f"Общий чат (Без топика)") if t_id else "Общий чат"
        
        if topic_name not in report:
            report[topic_name] = {"total": 0, "good": 0, "duplicates": 0, "no_text": 0}
            
        report[topic_name]["total"] += 1
        
        file_path = await msg.download_media(file=DOWNLOAD_DIR)
        
        try:
            img = Image.open(file_path)
            phash = str(imagehash.phash(img))
        except:
            if os.path.exists(file_path): os.remove(file_path)
            continue
            
        is_duplicate = False
        for known_hash, info in db.items():
            diff = imagehash.hex_to_hash(phash) - imagehash.hex_to_hash(known_hash)
            if diff <= 2:
                is_duplicate = True
                break
                
        if is_duplicate:
            report[topic_name]["duplicates"] += 1
            os.remove(file_path)
            continue
            
        text = get_text_from_image(file_path)
        expanded = any(kw.lower() in text.lower() for kw in SUCCESS_KEYWORDS if kw != "Яблоко")
        
        if expanded:
            report[topic_name]["good"] += 1
            new_hashes_this_run[phash] = {
                "date": msg.date.strftime("%Y-%m-%d %H:%M"),
                "topic": topic_name
            }
        else:
            report[topic_name]["no_text"] += 1
            
        os.remove(file_path)
        
    db.update(new_hashes_this_run)
    save_db(db)
    
    print("\n\n=== ИТОГОВЫЙ ОТЧЕТ ПО ТОПИКАМ ===")
    for t_name, stats in report.items():
        print(f"\n📂 Топик: {t_name}")
        print(f"  Всего прислано: {stats['total']}")
        print(f"  ✅ Идеальных: {stats['good']}")
        if stats['duplicates'] > 0:
            print(f"  ❌ ДУБЛИКАТОВ (жульничество): {stats['duplicates']}")
        if stats['no_text'] > 0:
            print(f"  ⚠️ Без распознанного текста: {stats['no_text']}")
            
    print("\nПроверка завершена! База данных обновлена.")

if __name__ == '__main__':
    asyncio.run(main())
