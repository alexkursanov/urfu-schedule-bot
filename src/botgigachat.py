import sys
import random
import httpx
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
from .config import Config, logger


def write_msg(vk, user_id, message):
    """Send a message to a user with required random_id parameter"""
    try:
        vk.method('messages.send', {
            'user_id': user_id, 
            'message': message,
            'random_id': random.randint(1, 2**31)
        })
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")


def get_giga_response(giga_client, user_message, system_prompt):
    """Get response from GigaChat with system prompt"""
    try:
        # Создаем список сообщений с системным промптом
        messages = [
            Messages(role=MessagesRole.SYSTEM, content=system_prompt),
            Messages(role=MessagesRole.USER, content=user_message)
        ]
        
        # Создаем запрос
        payload = Chat(messages=messages)
        
        # Отправляем запрос
        response = giga_client.chat(payload)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при запросе к GigaChat: {e}")
        return "Извините, произошла ошибка при обработке запроса. Попробуйте позже."


def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Запускаю бота в VK с GigaChat...")

    # Конфигурация бота
    config = Config()

    # Авторизуемся как сообщество в VK
    vk = vk_api.VkApi(token=config.VK_TOKEN)
    
    # Работа с сообщениями
    longpoll = VkLongPoll(vk)
    
    # Настройка HTTP клиента для GigaChat
    http_client = httpx.Client(verify=False)
    
    # Системный промпт (инструкция для бота)
    system_prompt = """
    Ты - дружелюбный помощник. Отвечаешь только на вопросы о расписании УрФУ!!!
    На другие вопросы не отвечай. Пиши, что это не твоя задача!!!
    ВАЖНО: Всегда начинай свой ответ со слова "Всмысле!!!", а затем давай основной ответ.
    Например: "Всмысле!!! Привет! Как я могу тебе помочь?"
    """
    
    # Инициализация GigaChat
    try:
        giga = GigaChat(
            credentials=config.GIGACHAT_TOKEN,
            verify_ssl_certs=False,
            http_client=http_client
        )
        logger.info("✅ GigaChat успешно инициализирован")
        logger.info(f"📝 Системный промпт: {system_prompt[:100]}...")
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации GigaChat: {e}")
        return
    
    # Основной цикл обработки сообщений
    logger.info("🤖 Бот запущен и ожидает сообщения...")
    
    try:
        for event in longpoll.listen():
            # Если пришло новое сообщение
            if event.type == VkEventType.MESSAGE_NEW:
                # Если оно имеет метку для меня (то есть бота)
                if event.to_me:
                    # Сообщение от пользователя
                    user_message = event.text
                    
                    # Логируем полученное сообщение
                    logger.info(f"📨 Получено сообщение от {event.user_id}: {user_message}")
                    
                    # Отправляем индикатор набора текста
                    try:
                        vk.method('messages.setActivity', {
                            'user_id': event.user_id,
                            'type': 'typing'
                        })
                    except:
                        pass
                    
                    # Получаем ответ от GigaChat с системным промптом
                    if user_message.strip():
                        response = get_giga_response(giga, user_message, system_prompt)
                        write_msg(vk, event.user_id, response)
                        logger.info(f"💬 Отправлен ответ: {response[:100]}...")
                    else:
                        write_msg(vk, event.user_id, "Пожалуйста, напишите текстовое сообщение.")
                        
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка в работе бота: {e}")
    finally:
        # Закрываем соединения
        http_client.close()
        logger.info("🔌 Соединения закрыты")


if __name__ == "__main__":
    print(f"Python interpreter: {sys.executable}")
    main()