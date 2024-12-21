import random
import json
import telebot
import requests
import os

TOKEN = "7936087407:AAGJVQlJe8LHgrFUxNQTOqG9QRGHGdAhhzE"
bot = telebot.TeleBot(TOKEN)

user_data = {}


def load_countries():
    with open("countries.json", "r", encoding="utf-8") as file:
        countries = json.load(file)

    country_data = []
    for country in countries:
        if 'flags' in country and 'name' in country:
            country_name = country['translations'].get('rus', {}).get('common', country['name']['common'])
            flag = country['flags']['png']
            country_data.append((country_name, flag))
    return country_data


country_flags = load_countries()


def download_image(image_url, save_path="./temp/"):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            name = image_url.split("/")[-1]
            save_path += name
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"Изображение сохранено: {save_path}")
            return save_path
        else:
            print(f"Ошибка загрузки изображения: {response.status_code}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def send_flag_image(chat_id, flag_url):
    try:
        img = download_image(flag_url)
        with open(img, 'rb') as image_file:
            bot.send_photo(chat_id=chat_id, photo=image_file)
        os.remove(img)
    except:
        print('error')


def send_options(message, correct_answer):
    wrong_answers = random.sample([x[0] for x in country_flags if x[0] != correct_answer], 2)
    options = wrong_answers + [correct_answer]
    random.shuffle(options)

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for country in options:
        markup.add(country)

    flag_url = [cca2 for name, cca2 in country_flags if name == correct_answer][0]
    print(flag_url)
    send_flag_image(message.chat.id, flag_url)

    bot.send_message(message.chat.id, "Выбери страну:", reply_markup=markup)
    user_data[message.chat.id] = correct_answer


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'Привет! Давай играть в игру "Угадай флаг страны"! Напиши /play, чтобы начать.')


@bot.message_handler(commands=['play'])
def play(message):
    name, _ = random.choice(country_flags)
    send_options(message, name)


@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(message.chat.id, "Бот остановлен.")
    exit()  # Завершаем выполнение программы


# @bot.message_handler(func=lambda message: True)
# def handle_answer(message):
#     correct_answer = user_data.get(message.chat.id)
#
#     if correct_answer:
#         if message.text == correct_answer:
#             bot.send_message(message.chat.id, f"Правильно! Это флаг страны {correct_answer}. Еще: /play")
#         else:
#             bot.send_message(message.chat.id,
#                              f"Неправильно! Это флаг страны {correct_answer}. Попробуй еще раз > /play")

user_stats = {}  # Словарь {user_id: {"correct": 0, "total": 0}}

@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    # Получение правильного ответа для пользователя
    correct_answer = user_data.get(message.chat.id)

    # Если ответа ещё нет, вернуть
    if not correct_answer:
        bot.send_message(
            message.chat.id, "Сначала начните игру! Напишите /play."
        )
        return

    # Увеличиваем общее количество попыток
    user_id = message.chat.id
    if user_id not in user_stats:
        user_stats[user_id] = {"correct": 0, "total": 0}
    user_stats[user_id]["total"] += 1

    # Проверяем правильность ответа
    if message.text.lower() == correct_answer.lower():
        # Увеличиваем счётчик правильных ответов
        user_stats[user_id]["correct"] += 1
        bot.send_message(
            user_id,
            f"Правильно! Это флаг страны {correct_answer}. "
            f"Твоя статистика: {user_stats[user_id]['correct']} из {user_stats[user_id]['total']} правильных. "
            "Вот следующий вопрос!"
        )
    else:
        bot.send_message(
            user_id,
            f"Неправильно! Это флаг страны {correct_answer}. "
            f"Твоя статистика: {user_stats[user_id]['correct']} из {user_stats[user_id]['total']} правильных. "
            "Попробуй снова!"
        )

    # Возвращаем новый вопрос
    name, _ = random.choice(country_flags)
    user_data[user_id] = name  # Обновляем правильный ответ для нового вопроса
    send_options(message, name)


@bot.message_handler(func=lambda message: False)
def error(message):
    bot.send_message(message.chat.id, "Что-то пошло не так, попробуй снова!")


if __name__ == '__main__':
    bot.polling(none_stop=True)
