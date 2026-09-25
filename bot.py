import pyautogui
import time
import sys
import os
import datetime
import requests
import json
import random
import re
import pyperclip

# --- НАСТРОЙКИ ---
ITERATIONS = 5                    # Сколько видео прокомментировать
CONFIDENCE = 0.8                  # Точность поиска (0.8 - чтобы не путал с лайком)

TELEGRAM_BOT_TOKEN = "8979713384:AAHOjZYO7jUJWTr3ggbYsgd4jThWXZXYtRU"
TELEGRAM_CHAT_ID = "-1002993185724" # "Тик ток | Рабочий"
TG_TOPIC_DATA_PATH = "/Users/danilakonovalov/.gemini/antigravity/scratch/tiktok_bot/last_topics_all.json"
USE_TELEGRAM = True               # Измените на False, если не хотите отправлять в ТГ
SLEEP_MAC_AFTER = False           # Отправлять ли мак в сон после работы

# Настройки автозамены (шорткаты, которые вы настроите в macOS или iPhone)
SHORTCUTS = ['111', '222', '333', '444', '555', '666', '777', '888', '999', '101010', '1111', '2222', '3333', '4444', '5555']

def get_target_thread_id():
    try:
        with open(TG_TOPIC_DATA_PATH, "r") as f:
            data = json.load(f)
        topics = data.get(TELEGRAM_CHAT_ID, {}).get("names", [])
        if len(topics) >= 7:
            return topics[6]
    except Exception as e:
        print(f"[-] Ошибка чтения базы тем: {e}")
    return None

def send_screenshot_to_telegram(photo_path):
    thread_id = get_target_thread_id()
    if not thread_id:
        print("[-] Не удалось определить ID темы Telegram. Отправка отменена.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    print(f"[*] Отправляем скриншот в Telegram (Тема: {thread_id})...")
    try:
        with open(photo_path, 'rb') as photo:
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'message_thread_id': thread_id
            }
            files = {'photo': photo}
            r = requests.post(url, data=data, files=files)
            if r.status_code == 200:
                print(f"[+] Скриншот успешно отправлен в Telegram!")
            else:
                print(f"[-] Ошибка Telegram API: {r.text}")
    except Exception as e:
        print(f"[-] Ошибка сети при отправке: {e}")

def find_and_click(image_path, timeout=5, click_offset_y=0):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE, grayscale=True)
            if location:
                x, y = location
                x = int(x / 2)
                y = int(y / 2)
                pyautogui.click(x, y + click_offset_y)
                print(f"[+] Кликнул по {image_path}")
                return True
        except:
            pass
        time.sleep(0.5)
    print(f"[-] Не смог найти {image_path} за {timeout} сек.")
    return False

def get_iphone_center():
    try:
        script = 'tell application "System Events" to tell process "Видеоповтор iPhone" to get {position of window 1, size of window 1}'
        import subprocess
        out = subprocess.check_output(['osascript', '-e', script], text=True).strip()
        parts = [int(p.strip()) for p in out.split(',')]
        if len(parts) == 4:
            return (parts[0] + parts[2]//2, parts[1] + parts[3]//2)
    except:
        pass
    return None

def swipe_next_video(comment_loc=None):
    print("[*] Свайпаем к следующему видео...")
    if comment_loc:
        start_x = comment_loc[0] - 150
        start_y = comment_loc[1]
    else:
        center = get_iphone_center()
        if center:
            start_x, start_y = center[0], center[1]
        else:
            start_x, start_y = None, None

    if start_x and start_y:
        pyautogui.moveTo(start_x, start_y)
        time.sleep(0.2)
        
        # Сила скролла х2 (по просьбе)
        pyautogui.scroll(-3200)
        time.sleep(0.1)
        pyautogui.scroll(-3200)

def close_comments_and_swipe(comment_loc):
    print("[*] Закрываем комментарии...")
    if not find_and_click('close_icon.png', timeout=3):
        print("[-] Не нашли крестик. Кликаем в темную зону над комментами для закрытия.")
        if comment_loc:
            pyautogui.click(comment_loc[0] - 150, comment_loc[1] - 300)
            time.sleep(0.5)
            pyautogui.click(comment_loc[0] - 150, comment_loc[1] - 300)
    time.sleep(0.5) # Сократили с 1.5
    swipe_next_video(comment_loc)
    time.sleep(2.5) # Сократили с 4.0

def main():
    global ITERATIONS, USE_TELEGRAM, SLEEP_MAC_AFTER
    
    print("\n=== НАСТРОЙКА ЗАПУСКА ===")
    ans = input("Отправлять скриншоты в Telegram? (y/n) [по умолчанию Y]: ").strip().lower()
    if ans == 'n' or ans == 'нет':
        USE_TELEGRAM = False
    else:
        USE_TELEGRAM = True
        
    iters_str = input(f"Сколько успешных комментариев сделать? [по умолчанию {ITERATIONS}]: ").strip()
    if iters_str.isdigit():
        ITERATIONS = int(iters_str)
        
    ans_sleep = input("Усыпить Макбук после завершения работы? (y/n) [по умолчанию N]: ").strip().lower()
    if ans_sleep == 'y' or ans_sleep == 'да':
        SLEEP_MAC_AFTER = True
    else:
        SLEEP_MAC_AFTER = False

    print("\n=============================================")
    print(f"🤖 БОТ ЗАПУСКАЕТСЯ! Задача: {ITERATIONS} успешных комментов.")
    print(f"Телеграм: {'ВКЛ' if USE_TELEGRAM else 'ВЫКЛ'} | Сон после завершения: {'ВКЛ' if SLEEP_MAC_AFTER else 'ВЫКЛ'}")
    print("У ВАС 3 СЕКУНДЫ: Быстро переключитесь на окно Видеоповтора и ничего не трогайте!")
    print("=============================================\n")
    time.sleep(3)
    
    global_start_time = time.time()
    
    successful_comments = 0
    attempts = 0
    consecutive_fails = 0
    
    while successful_comments < ITERATIONS:
        attempts += 1
        consecutive_fails += 1
        
        if consecutive_fails > 15:
            print("\n[!!!] АВАРИЙНАЯ ОСТАНОВКА: Бот пропустил 15 видео подряд (реклама, глюки или закрытые комменты).")
            print("[!!!] Скорее всего что-то пошло не так. Останавливаем работу для безопасности!")
            break
            
        if consecutive_fails >= 3:
            print("[!] Несколько неудач подряд. Проверяем, не вылезла ли кнопка 'Повтор' (конец рекламы)...")
            try:
                loc_replay = pyautogui.locateCenterOnScreen('replay_icon.png', confidence=0.8, grayscale=True)
                if loc_replay:
                    print("[*] Найдена кнопка 'Повтор'! Кликаем, чтобы убрать оверлей, и свайпаем...")
                    pyautogui.click(int(loc_replay[0]/2), int(loc_replay[1]/2))
                    time.sleep(1.0)
                    swipe_next_video()
                    time.sleep(2.5)
                    continue
            except:
                pass
            
        print(f"\n--- Попытка {attempts} (Успешных комментов: {successful_comments}/{ITERATIONS}) ---")
        time.sleep(1.0) # Даем видео загрузиться
        
        # --- ПРОВЕРКА НА РЕКЛАМУ ---
        try:
            loc_ad = pyautogui.locateCenterOnScreen('ad_badge.png', confidence=0.75, grayscale=True)
            loc_ad_btn = pyautogui.locateCenterOnScreen('ad_button.png', confidence=0.75, grayscale=True)
            
            if loc_ad or loc_ad_btn:
                print("[!] Найдена реклама! Пропускаем видео...")
                swipe_next_video()
                time.sleep(2.5) 
                continue
        except:
            pass
        
        print("[*] Ищем видео и ставим на паузу...")
        start_time = time.time()
        comment_loc = None
        while time.time() - start_time < 5:
            try:
                loc = pyautogui.locateCenterOnScreen('comment_icon.png', confidence=0.85)
                if loc:
                    comment_loc = (int(loc[0]/2), int(loc[1]/2))
                    break
            except:
                pass
            time.sleep(0.5)
            
        if not comment_loc:
            print("[-] Остановка: не нашли иконку комментария.")
            pyautogui.screenshot("/Users/danilakonovalov/Pictures/TikTok_Screenshots/debug_not_found.png")
            print("[i] Сохранен снимок экрана в Изображения/TikTok_Screenshots/debug_not_found.png для проверки!")
            swipe_next_video()
            time.sleep(2.5)
            continue
            
        # Мы убрали предварительный клик-паузу, так как он иногда случайно попадал
        # по кнопке "на весь экран" у горизонтальных видео.
        
        # Открываем комменты (видео все равно уйдет на фон)
        print("[*] Открываем комментарии...")
        pyautogui.click(comment_loc[0], comment_loc[1])
        time.sleep(2.0) # Вернули ожидание шторки
        
        if not find_and_click('input_field.png', timeout=5):
            print("[!] Комментарии отключены автором (или поле ввода не найдено). Пропускаем видео...")
            close_comments_and_swipe(comment_loc)
            continue
            
        time.sleep(1.5) # Вернули ожидание клавиатуры
        
        shortcut = random.choice(SHORTCUTS)
        print(f"[*] Печатаем автозамену: {shortcut}")
        
        pyautogui.write(' ' + shortcut, interval=0.1)
        time.sleep(0.2) # Пауза перед пробелом (сократили с 0.5)
        pyautogui.press('space') 
        time.sleep(1.5) # Ожидание развертывания автозамены (сократили с 2.0)
        
        print("[*] Отправляем...")
        pyautogui.press('enter')
        time.sleep(3.0) # Вернули ожидание отправки коммента
        
        print("[*] Ищем наш коммент, чтобы лайкнуть...")
        try:
            hearts = list(pyautogui.locateAllOnScreen('heart_icon.png', confidence=0.8, grayscale=True))
            if hearts:
                hearts.sort(key=lambda h: h.top)
                first_heart = hearts[0]
                hx = int((first_heart.left + first_heart.width / 2) / 2)
                hy = int((first_heart.top + first_heart.height / 2) / 2)
                pyautogui.click(hx, hy)
                print("[+] Поставили лайк на свой комментарий! ❤️")
                time.sleep(0.5) # Сократили с 1.0
            else:
                print("[-] Сердечек на экране не найдено")
        except Exception as e:
            print(f"[-] Ошибка при поиске лайка: {e}")
            
        print("[*] Делаем скриншот...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        base_dir = "/Users/danilakonovalov/Pictures/TikTok_Screenshots"
        folder_name = f"{base_dir}/sent" if USE_TELEGRAM else f"{base_dir}/unsent"
        os.makedirs(folder_name, exist_ok=True)
        
        region = None
        try:
            script = 'tell application "System Events" to tell process "Видеоповтор iPhone" to get {position of window 1, size of window 1}'
            import subprocess
            out = subprocess.check_output(['osascript', '-e', script], text=True).strip()
            parts = [int(p.strip()) for p in out.split(',')]
            if len(parts) == 4:
                pad_left = 7
                pad_right = 7
                pad_top = 35
                pad_bottom = 8
                
                region = (
                    parts[0] + pad_left, 
                    parts[1] + pad_top, 
                    parts[2] - pad_left - pad_right, 
                    parts[3] - pad_top - pad_bottom
                )
        except Exception:
            pass
            
        screenshot_path = os.path.abspath(os.path.join(folder_name, f"comment_{timestamp}.jpg"))
        img = pyautogui.screenshot(region=region)
        img = img.convert('RGB') # JPG не поддерживает прозрачность
        img.save(screenshot_path, "JPEG", quality=85)
        print(f"[+] Скриншот сохранен локально: {screenshot_path}")
        
        if USE_TELEGRAM:
            send_screenshot_to_telegram(screenshot_path)
        
        close_comments_and_swipe(comment_loc)
        
        # Если мы дошли до сюда, значит коммент успешно отправлен!
        successful_comments += 1
        consecutive_fails = 0
        
    total_time = time.time() - global_start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
        
    print("\n✅ РАБОТА ЗАВЕРШЕНА! Бот отключился.")
    print(f"⏱  Затрачено времени: {minutes} мин {seconds} сек.")
    
    if SLEEP_MAC_AFTER:
        print("💤 Отправляю Макбук в спящий режим...")
        time.sleep(2)
        os.system("pmset sleepnow")

if __name__ == "__main__":
    os.makedirs("/Users/danilakonovalov/Pictures/TikTok_Screenshots", exist_ok=True)
    main()
