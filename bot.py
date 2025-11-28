import telebot
import requests
import json
import time
from Class_ModelResponse import ModelResponse, ChoiceResponse, MessageResponse, UsageResponse

API_TOKEN = '8233072556:AAEg91bVzUM2mAA_GHk-Fc9DsV2GByFzq9c'
bot = telebot.TeleBot(API_TOKEN)

# Контекст пользователя
user_contexts = {}

def get_model_response(user_id: int, user_message: str) -> str:

    # Инициализирование контекста для нового пользователя
    if user_id not in user_contexts:
        user_contexts[user_id] = []
        print(f"Создан новый контекст для пользователя {user_id}")
    
    # Системное сообщение добавляется, если контекст пустой
    if len(user_contexts[user_id]) == 0:
        user_contexts[user_id].append({
            "role": "system",
            "content": "Ты полезный ассистент. Веди естественный диалог, учитывая всю историю разговора. Отвечай на вопросы, опираясь на предыдущие сообщения, и явно ссылайся на контекст когда это уместно."
        })
    
    # Новое сообщение пользователя добавляется в контекст
    user_contexts[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    if len(user_contexts[user_id]) > 8:
        system_msg = user_contexts[user_id][0] if user_contexts[user_id][0].get('role') == 'system' else None
        if system_msg:
            user_contexts[user_id] = [system_msg] + user_contexts[user_id][-7:]
        else:
            user_contexts[user_id] = user_contexts[user_id][-8:]
        print(f"Контекст пользователя {user_id} обрезан до 8 сообщений")
    
    request_data = {
        "messages": user_contexts[user_id],
        "temperature": 0.7,
        "max_tokens": 256,  
        "stream": False
    }
    
    try:
        print(f"Отправка запроса для пользователя {user_id}")
        print(f"Текущее сообщение: {user_message}")
        print(f"Размер контекста: {len(user_contexts[user_id])} сообщений")
        
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:1234/v1/chat/completions',
            json=request_data,
            timeout=120  
        )
        
        end_time = time.time()
        print(f"Время ответа: {end_time - start_time:.2f} секунд")
        
        if response.status_code == 200:
            model_response = parse_model_response(response.json())
            
            if model_response.choices and len(model_response.choices) > 0:
                assistant_reply = model_response.choices[0].message.content
                
                # Ответ ассистента добавляется в контекст
                user_contexts[user_id].append({
                    "role": "assistant",
                    "content": assistant_reply
                })
                
                print(f"Получен ответ от модели для пользователя {user_id}")
                print(f"Ответ: {assistant_reply}")
                
                # Логирование статистики токенов
                if hasattr(model_response, 'usage'):
                    usage = model_response.usage
                    print(f"Использовано токенов: {usage.total_tokens}")
                
                return assistant_reply
            else:
                error_msg = "Модель не вернула ответ."
                print(error_msg)
                return error_msg
        else:
            error_msg = f"Ошибка API: {response.status_code}"
            print(f"Ответ сервера: {response.text}")
            return error_msg
            
    except requests.exceptions.ConnectionError:
        error_msg = "Не удалось подключиться к LM Studio. Убедитесь, что сервер запущен на localhost:1234"
        print(error_msg)
        return error_msg
    except requests.exceptions.Timeout:
        error_msg = "Превышено время ожидания ответа от модели. Попробуйте сократить запрос или подождите."
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Произошла непредвиденная ошибка: {str(e)}"
        print(error_msg)
        return error_msg

def parse_model_response(response_data):

    try:
        data = response_data
        
        usage_data = data.get('usage', {})
        usage = UsageResponse(
            prompt_tokens=usage_data.get('prompt_tokens', 0),
            completion_tokens=usage_data.get('completion_tokens', 0),
            total_tokens=usage_data.get('total_tokens', 0)
        )
        
        choices = []
        for choice_data in data.get('choices', []):
            message_data = choice_data.get('message', {})
            message = MessageResponse(
                role=message_data.get('role', ''),
                content=message_data.get('content', '')
            )
            choice = ChoiceResponse(
                index=choice_data.get('index', 0),
                message=message,
                logprobs=choice_data.get('logprobs'),
                finish_reason=choice_data.get('finish_reason', '')
            )
            choices.append(choice)
        
        # Создаем основной объект ответа
        model_response = ModelResponse(
            id=data.get('id', ''),
            object=data.get('object', ''),
            created=data.get('created', 0),
            model=data.get('model', ''),
            choices=choices,
            usage=usage,
            system_fingerprint=data.get('system_fingerprint', '')
        )
        
        return model_response
    except Exception as e:
        raise ValueError(f"Ошибка парсинга ответа модели: {str(e)}")

def get_context_stats(user_id: int) -> str:

    if user_id not in user_contexts:
        return "Контекст пуст"
    
    context = user_contexts[user_id]
    user_messages = len([msg for msg in context if msg.get('role') == 'user'])
    assistant_messages = len([msg for msg in context if msg.get('role') == 'assistant'])
    system_messages = len([msg for msg in context if msg.get('role') == 'system'])
    total_messages = len(context)
    
    return (f"Статистика контекста:\n"
            f"• Всего сообщений: {total_messages}\n"
            f"• Вопросы пользователя: {user_messages}\n"
            f"• Ответы ассистента: {assistant_messages}\n"
            f"• Системные: {system_messages}")

def show_full_context(user_id: int) -> str:

    if user_id not in user_contexts or len(user_contexts[user_id]) <= 1:  # Только системное сообщение
        return "История диалога пуста"
    
    history = "Полная история диалога:\n\n"
    for i, msg in enumerate(user_contexts[user_id]):
        if msg.get('role') == 'system':
            continue  # Пропуск системного сообщения в выводе
        
        role = "👤 Вы" if msg.get('role') == 'user' else "🤖 Бот"
        content = msg.get('content', '')
        history += f"{role}: {content}\n\n"
    
    return history

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    # Контекст при команде /start очищается
    user_contexts[user_id] = []
    print(f"Контекст пользователя {user_id} ({username}) полностью очищен")
    
    welcome_text = (
        "Привет! Я ваш Telegram бот с системой контекста.\n"
        "Запоминаю историю нашего разговора и учитываю её в ответах!\n\n"

        "Как я работаю:\n"
        "1. Задайте вопрос (лучше на английском, например, 'What is the most popular film in Italy nowadays?')\n"
        "2. Задайте уточняющий вопрос (например, 'Why?')\n"
        "3. Я отвечу с учетом предыдущего разговора!\n\n"
        "Доступные команды:\n"
        "/start - начать новый диалог (очистить контекст)\n"
        "/model - информация о модели\n"
        "/clear - очистить историю\n"
        "/context - статистика контекста\n"
        "/history - показать всю историю диалога\n\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['model'])
def send_model_name(message):
    try:
        response = requests.get('http://localhost:1234/v1/models', timeout=10)
        
        if response.status_code == 200:
            model_info = response.json()
            model_name = model_info['data'][0]['id']
            bot.reply_to(message, f"Используемая модель: {model_name}")
        else:
            bot.reply_to(message, f'Не удалось получить информацию о модели. Статус: {response.status_code}')
            
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, 'Не удалось подключиться к LM Studio.')
    except Exception as e:
        bot.reply_to(message, f'Ошибка: {str(e)}')

@bot.message_handler(commands=['clear'])
def clear_context(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    
    user_contexts[user_id] = []
    print(f"Контекст пользователя {user_id} ({username}) очищен")
    bot.reply_to(message, "История диалога полностью очищена! Контекст сброшен.")

@bot.message_handler(commands=['context'])
def show_context(message):
    user_id = message.from_user.id
    stats = get_context_stats(user_id)
    bot.reply_to(message, stats)

@bot.message_handler(commands=['history'])
def show_history(message):
    user_id = message.from_user.id
    history = show_full_context(user_id)
    bot.reply_to(message, history)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_message = message.text
    username = message.from_user.username or f"user_{user_id}"
    
    print(f"👤 Получено сообщение от {username} ({user_id}): {user_message}")
    
    # Статус "печатает"
    bot.send_chat_action(message.chat.id, 'typing')
    
    response_text = get_model_response(user_id, user_message)
    bot.reply_to(message, response_text)

if __name__ == '__main__':
    print("Бот запущен...")
    print("LM Studio: localhost:1234")
    print("Учитывается контекст диалога")
    print("Можно посмотреть историю чата")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")