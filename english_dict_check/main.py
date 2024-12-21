import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Путь к файлу со словарём
path_english_dict = "D://_teach//_obsidian//Riman//English dict.md"

# Словарь статистики
user_stats = {}


# Функция для чтения файла с переводами
def load_words(file_path):
    words = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '-' in line:
                parts = line.strip().split(' - ')
                english = parts[0].split(', ')
                russian = parts[1].split(', ')
                words.append((english, russian))
    return words


# Глобальная переменная для хранения словаря
words = load_words(path_english_dict)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Сбрасываем статистику при старте
    user_stats[user_id] = {"total": 0, "correct": 0, "mode": None, "in_training": False}

    # Генерируем меню для выбора режима
    keyboard = [
        [InlineKeyboardButton("Английский ➡️ Русский", callback_data="en_ru")],
        [InlineKeyboardButton("Русский ➡️ Английский", callback_data="ru_en")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет! Я бот для изучения слов. Выбери режим для начала тренировки:",
        reply_markup=reply_markup
    )


# Обработка выбора режима
async def select_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    mode = query.data

    if mode == "en_ru":
        user_stats[user_id]["mode"] = 1
        await query.edit_message_text("Режим тренировок: Английский ➡️ Русский")
    elif mode == "ru_en":
        user_stats[user_id]["mode"] = 2
        await query.edit_message_text("Режим тренировок: Русский ➡️ Английский")

    # Начало тренировки после выбора режима
    user_stats[user_id]["in_training"] = True
    await start_training(update, context)


# Команда /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_stats[user_id]["in_training"] = False
    stats = user_stats[user_id]
    await update.message.reply_text(
        f"Тренировка остановлена!\nВерно решено: {stats['correct']} из {stats['total']} вопросов."
    )


# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats = user_stats.get(user_id, {"total": 0, "correct": 0})

    await update.message.reply_text(
        f"Текущая статистика:\n"
        f"Всего вопросов: {stats['total']}\n"
        f"Правильных ответов: {stats['correct']}\n"
        f"Процент правильных: {round((stats['correct'] / stats['total']) * 100, 2) if stats['total'] > 0 else 0}%."
    )


# Начало тренировки
async def start_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    # Проверяем, активна ли тренировка
    if not user_stats[user_id]["in_training"]:
        return

    mode = user_stats[user_id]["mode"]

    random_entry = random.choice(words)
    if mode == 1:  # Английский на русский
        word = random.choice(random_entry[0])
        correct_answer = random.choice(random_entry[1])
        options = random.sample([w for _, trans in words for w in trans], 3) + [correct_answer]
    elif mode == 2:  # Русский на английский
        word = random.choice(random_entry[1])
        correct_answer = random.choice(random_entry[0])
        options = random.sample([w for trans, _ in words for w in trans], 3) + [correct_answer]

    random.shuffle(options)

    # Сохраняем текущий вопрос

    context.user_data["current_question"] = {"word": word, "correct": correct_answer}

    # Генерируем варианты ответа
    keyboard = [[InlineKeyboardButton(option, callback_data=option)] for option in options]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"Переведи: *{word}*",
        reply_markup=reply_markup
    )


# Обработка ответа
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    # Активна ли тренировка?
    if not user_stats[user_id]["in_training"]:
        return

    user_stats[user_id]["total"] += 1
    current_question = context.user_data.get("current_question", {})
    correct_answer = current_question.get("correct", None)

    # Проверяем ответ
    if query.data == correct_answer:
        user_stats[user_id]["correct"] += 1
        await query.edit_message_text("Правильно! 🎉 Следующий вопрос...")
    else:
        await query.edit_message_text(f"Неправильно 😔 Верный ответ: {correct_answer}. Следующий вопрос...")

    # Следующий вопрос
    await start_training(update, context)


# Основная функция запуска бота
def main():
    # Создаём приложение
    app = Application.builder().token("7936087407:AAGJVQlJe8LHgrFUxNQTOqG9QRGHGdAhhzE").build()

    # Обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("stats", stats))

    # Обработчики кнопок
    app.add_handler(CallbackQueryHandler(select_mode, pattern="^(en_ru|ru_en)$"))
    app.add_handler(CallbackQueryHandler(handle_answer))

    # Запуск бота
    app.run_polling()


if __name__ == "__main__":
    main()
