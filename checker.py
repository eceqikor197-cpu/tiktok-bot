import os
import subprocess

def get_text_from_image(image_path):
    script_path = os.path.join(os.path.dirname(__file__), 'ocr.swift')
    try:
        out = subprocess.check_output(['swift', script_path, image_path], text=True)
        return out
    except Exception as e:
        return ""

from datetime import datetime, timedelta

def parse_filename_time(filename):
    # Ожидаемый формат: comment_YYYY-MM-DD_HH-MM-SS.jpg
    try:
        time_str = filename.split('_', 1)[1].rsplit('.', 1)[0]
        return datetime.strptime(time_str, "%Y-%m-%d_%H-%M-%S")
    except:
        return None

def main():
    screenshots_dir = "/Users/danilakonovalov/Pictures/TikTok_Screenshots/unsent"
    if not os.path.exists(screenshots_dir):
        print(f"Папка {screenshots_dir} не найдена.")
        return
        
    success_keywords = [
        "Долго искал", "Тоже долго", "Кстати, для подготовки", "нормальные варианты",
        "сильные преподаватели", "перешел на Яблоко", "спасаюсь через", "много хорошего про",
        "друзья посоветовали", "топовую подготовку", "Никак не мог определиться",
        "адекватное по стоимости", "Часто вижу рекомендации", "реально полезные",
        "Перепробовал кучу", "Яблоко"
    ]
    fail_keywords = ['111', '222', '333', '444', '555', '666', '777', '888', '999', '101010', '1111', '2222', '3333', '4444', '5555']
    
    files = [f for f in os.listdir(screenshots_dir) if f.endswith('.png') or f.endswith('.jpg')]
    if not files:
        print("В папке unsent нет скриншотов для проверки.")
        return
        
    # Парсим время и сортируем
    files_with_time = []
    for f in files:
        dt = parse_filename_time(f)
        if dt:
            files_with_time.append((dt, f))
            
    files_with_time.sort(key=lambda x: x[0])
    
    # Разбиваем на сессии (разрыв более 3 минут = новая сессия)
    sessions = []
    current_session = []
    for dt, f in files_with_time:
        if not current_session:
            current_session.append((dt, f))
        else:
            prev_dt = current_session[-1][0]
            if (dt - prev_dt).total_seconds() <= 180: # 3 минуты
                current_session.append((dt, f))
            else:
                sessions.append(current_session)
                current_session = [(dt, f)]
    if current_session:
        sessions.append(current_session)
        
    print(f"Найдено скриншотов: {len(files_with_time)}")
    print(f"Выделено рабочих сессий (заходов): {len(sessions)}\n")
    print("Запускаю нейросеть Apple Vision для проверки качества... (может занять пару минут)\n")
    
    total_success = 0
    total_fail = 0
    total_unknown = 0
    
    for i, sess in enumerate(sessions):
        start_t = sess[0][0].strftime("%d.%m %H:%M")
        end_t = sess[-1][0].strftime("%H:%M")
        print(f"=== ЗАХОД {i+1} (с {start_t} до {end_t} | Комментов: {len(sess)}) ===")
        
        for dt, f in sess:
            path = os.path.join(screenshots_dir, f)
            text = get_text_from_image(path)
            
            expanded = any(kw.lower() in text.lower() for kw in success_keywords if kw != "Яблоко")
            failed_expansion = any(f"\n{kw}\n" in text or f"\n{kw} " in text for kw in fail_keywords)
            
            time_str = dt.strftime("%H:%M:%S")
            if expanded:
                print(f"  ✅ {time_str} - Успешно")
                total_success += 1
            elif failed_expansion:
                print(f"  ❌ {time_str} - БРАК (голые цифры)")
                total_fail += 1
            else:
                print(f"  ⚠️ {time_str} - Неясно (перекрыто/не распознано)")
                total_unknown += 1
        print("") # пустая строка между сессиями
            
    print(f"=== ОБЩИЕ ИТОГИ ПРОВЕРКИ ===")
    print(f"Всего скриншотов: {len(files_with_time)}")
    print(f"✅ Идеальных: {total_success}")
    print(f"❌ Бракованных: {total_fail}")
    print(f"⚠️ Непонятных: {total_unknown}")

if __name__ == "__main__":
    main()
