import random
import json
import os
from datetime import datetime, timedelta
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from .config import Config, logger


def write_msg(vk, user_id, message, keyboard=None):
    """Отправка сообщения с поддержкой клавиатуры"""
    params = {
        'user_id': user_id,
        'message': message,
        'random_id': random.randint(1, 2**31)
    }
    if keyboard:
        params['keyboard'] = keyboard
    vk.method('messages.send', params)

def get_schedule(group, day=None):
    """
    Получение расписания для группы
    Здесь будет логика парсинга расписания
    """
    # Пока заглушка — позже заменим на реальный парсер
    schedule_data = {
        'понедельник': '📚 10:00 — Математика\n📖 12:00 — Физика',
        'вторник': '💻 10:00 — Программирование\n📊 14:00 — Базы данных',
        'среда': '📈 11:00 — Статистика\n🎓 13:00 — Семинар',
        'четверг': '🌐 09:00 — Web-разработка\n🤖 15:00 — Машинное обучение',
        'пятница': '📝 10:00 — Лабораторная работа\n🎯 12:00 — Проектная деятельность',
    }
    
    if day:
        return schedule_data.get(day.lower(), 'Нет расписания на этот день')
    return schedule_data

def save_user_group(user_id, group):
    """Сохранение выбранной группы пользователя"""
    # Простое сохранение в JSON файл
    users_file = 'users.json'
    
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}
    
    users[str(user_id)] = group
    
    with open(users_file, 'w') as f:
        json.dump(users, f)

def get_user_group(user_id):
    """Получение группы пользователя"""
    try:
        with open('users.json', 'r') as f:
            users = json.load(f)
            return users.get(str(user_id))
    except FileNotFoundError:
        return None

def main():
    """Основная функция запуска бота"""
    print("🚀 Запускаю бота с расписанием...")

    # Конфигурация бота
    config = Config()
    
    # Авторизация
    vk = vk_api.VkApi(token=config.VK_TOKEN)
    longpoll = VkLongPoll(vk)
    
    # Основной цикл обработки сообщений
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = event.user_id
            request = event.text.lower().strip()
            
            # Обработка команд
            if request == 'начать' or request == '/start':
                write_msg(vk, user_id, 
                    "👋 Привет! Я бот расписания.\n\n"
                    "📌 Доступные команды:\n"
                    "• установить группа [номер] — выбрать группу\n"
                    "• расписание [день] — посмотреть расписание\n"
                    "• сегодня — расписание на сегодня\n"
                    "• завтра — расписание на завтра\n"
                    "• неделя — расписание на неделю")
            
            elif request.startswith('установить группа'):
                # Установка группы пользователя
                try:
                    group = request.split('группа')[1].strip()
                    save_user_group(user_id, group)
                    write_msg(vk, user_id, f"✅ Группа {group} сохранена!")
                except:
                    write_msg(vk, user_id, "❌ Ошибка! Используйте формат: установить группа ИН-123")
            
            elif request == 'сегодня':
                today = datetime.now().strftime('%A')
                # Конвертируем день недели на русский
                days_ru = {
                    'Monday': 'понедельник', 'Tuesday': 'вторник',
                    'Wednesday': 'среда', 'Thursday': 'четверг',
                    'Friday': 'пятница', 'Saturday': 'суббота',
                    'Sunday': 'воскресенье'
                }
                day_ru = days_ru.get(today, 'понедельник')
                schedule = get_schedule(None, day_ru)
                write_msg(vk, user_id, f"📅 Расписание на {day_ru}:\n{schedule}")
            
            elif request == 'завтра':
                tomorrow = (datetime.now() + timedelta(days=1)).strftime('%A')
                days_ru = {
                    'Monday': 'понедельник', 'Tuesday': 'вторник',
                    'Wednesday': 'среда', 'Thursday': 'четверг',
                    'Friday': 'пятница', 'Saturday': 'суббота',
                    'Sunday': 'воскресенье'
                }
                day_ru = days_ru.get(tomorrow, 'вторник')
                schedule = get_schedule(None, day_ru)
                write_msg(vk, user_id, f"📅 Расписание на {day_ru}:\n{schedule}")
            
            elif request.startswith('расписание'):
                # Получение расписания на конкретный день
                if len(request.split()) > 1:
                    day = request.split()[1]
                    schedule = get_schedule(None, day)
                    write_msg(vk, user_id, f"📅 Расписание на {day}:\n{schedule}")
                else:
                    write_msg(vk, user_id, "❌ Укажите день: расписание понедельник")
            
            elif request == 'неделя':
                schedule = get_schedule(None)
                response = "📅 **Расписание на неделю:**\n\n"
                for day, lessons in schedule.items():
                    response += f"**{day.capitalize()}:**\n{lessons}\n\n"
                write_msg(vk, user_id, response)
            
            elif request == 'помощь':
                write_msg(vk, user_id,
                    "📌 **Доступные команды:**\n"
                    "• установить группа ИН-123 — выбрать группу\n"
                    "• расписание понедельник — расписание на день\n"
                    "• сегодня — расписание на сегодня\n"
                    "• завтра — расписание на завтра\n"
                    "• неделя — полное расписание\n"
                    "• помощь — показать эту справку")
            
            else:
                user_group = get_user_group(user_id)
                if user_group:
                    write_msg(vk, user_id, 
                        f"❓ Не понял запрос. Введите 'помощь' для списка команд.\n"
                        f"Ваша группа: {user_group}")
                else:
                    write_msg(vk, user_id,
                        "❓ Привет! Сначала укажите вашу группу:\n"
                        "установить группа ИН-123")

if __name__ == "__main__":
    main()