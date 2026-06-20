from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (
    load_message,
    send_text,
    send_image,
    show_main_menu,
    default_callback_handler,
    load_prompt,
    send_text_buttons,
    analyze_audio,
    generate_audio_response
)

import credentials


# ==================== СТАРТ ТА ГОЛОВНІ РЕЖИМИ ====================


# Кнопки для головного меню /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, 'main')
    await send_text(update, context, load_message('main'))

    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓',
        'resume': 'Допомога з резюме 🖋️',
        'chat': "Голосовий GPTChat ✨"
    })

# Кнопки для /random
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, 'random')

    response = await chat_gpt.send_question(load_prompt('random'), 'Давай рандомний факт!')

    await send_text_buttons(
        update,
        context,
        response,
        buttons={
                    'random_finish': 'Закінчити',
                    'random_one_more': 'Хочу ще факт'
                }
    )

# Кнопка дял /gpt
async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))

    context.user_data['mode'] = 'gpt'

# Кнопки для /talk
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, 'talk')

    context.user_data['mode'] = 'talk'

    await send_text_buttons(
        update,
        context,
        load_message('talk'),
        buttons={
            'talk_cobain': 'Курт Кобейн',
            'talk_queen': 'Єлизавета II',
            'talk_tolkien': 'Джон Толкін',
            'talk_nietzsche': 'Фрідріх Ніцше',
            'talk_hawking': 'Стівен Гокінг'
        }
    )

# Кнопки для /quiz
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, 'quiz')
    context.user_data['mode'] = 'quiz'
    context.user_data['score'] = 0

    await send_text_buttons(
        update,
        context,
        load_message('quiz'),
        buttons={
                    'quiz_prog': "Програмування Python 🐍",
                    'quiz_math': "Математичні теорії 📐",
                    'quiz_biology': "Біологія 🌿",
                    'random_finish': "Назад"
                }
    )
    # Лічильник правильних відповідей
    context.user_data['score'] += 1

# Кнопка для /resume — сброс и старт первого вопроса
async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, 'resume')
    context.user_data['mode'] = 'resume'

    # Инициализируем счетчик и массив для ответов
    context.user_data['resume_step'] = 0
    context.user_data['resume_answers'] = []

    # Загружаем список вопросов из файла по строкам
    questions = load_message('resume_questions').strip().split('\n')

    if not questions:
        await send_text(
            update,
            context,
            text="Файл питань пустий"
        )
        return

    context.user_data['resume_questions'] = questions

    # Приветствие и первый вопрос
    await send_text_buttons(
        update,
        context,
        f"Привет! Давай составим резюме. Ответь на 10 вопросов.\n\n{questions[0]}",
        buttons={
            'resume_finish': "Назад"
        }
    )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    context.user_data['mode'] = 'chat'

    await send_image(update, context, 'image_chat')

    await send_text_buttons(
        update,
        context,
        load_message('message_chat'),
        buttons={
            'random_finish': "Назад"
        }
    )


# ==================== ДИСПЕТЧЕР КНОПОК ====================
# Логіка натискання кнопок у /random
async def random_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_random = update.callback_query.data

    if query_random == 'random_one_more':
        await random(update, context)
    else:
        await start(update, context)


# Логіка натискання кнопок у /talk
async def talk_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_talk = update.callback_query.data

    if query_talk in ['talk_cobain', 'talk_queen', 'talk_tolkien', 'talk_nietzsche', 'talk_hawking']:
        context.user_data['talk_prompt'] = query_talk
        await send_text(update, context, f"Напишіть повідомлення для співрозмовника.")


# Логіка натискання кнопок у /quiz
async def quiz_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    query = update.callback_query.data

    if query == 'start':
        await start(update, context)
    elif query == 'quiz':
        await quiz(update, context)
    elif query == 'quiz_more':
        await quiz_button(update, context)
    else:
        context.user_data['quiz_topic'] = query
        await quiz_button(update, context)

async def quiz_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = await chat_gpt.send_question(load_prompt('quiz'), context.user_data.get('quiz_topic'))
    await send_text(update, context, question)


# ==================== ОБРОБКА ПОВІДОМЛЕНЬ ====================
async def gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await chat_gpt.send_question("", update.effective_message.text)

    await send_text_buttons(
        update,
        context,
        response,
        {
            'random_finish': "Назад"
        }
    )


async def talk_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = context.user_data.get('talk_prompt')
    response = await chat_gpt.send_question(load_prompt(prompt), update.effective_message.text)
    await send_text_buttons(update, context, response, {'random_finish': 'Закінчити'})


async def quiz_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data.get('score', 0)
    await send_text(update, context, "Зачекайте, триває перевірка...")
    answer = await chat_gpt.add_message(update.effective_message.text)

    # Лічильник
    if answer == "Правильно!":
        # Безпечний лічильник відповідей
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        await send_text(update, context, f"Ваших правильних відповідей: {score}")

    await send_text_buttons(
        update,
        context,
        answer,
           {
               'quiz_more': "Нове питання",
               'quiz': "Назад"
           }
      )


async def resume_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Натискання кнопки НАЗАД
    if update.callback_query:
        await update.callback_query.answer()
        context.user_data['mode'] = None
        await start(update, context)
        return

    # Дістаємо поточний стан опитування
    step = context.user_data.get('resume_step', 0)
    questions = context.user_data.get('resume_questions', [])
    answers = context.user_data.get('resume_answers', [])

    # Зберігаємо поточну відповідь
    answers.append(
        f"Питання: {questions[step]}\nВідповідь: {update.effective_message.text}"
    )
    step += 1
    context.user_data['resume_step'] = step

    # Якщо відповіли ще не на всі запитання — задаємо наступний
    if step < len(questions):
        await send_text_buttons(
            update,
            context,
            text=f"{questions[step]}",
            buttons={
                'resume_finish': 'Назад'
            }
        )
        return

    # Якщо відповіли на всі питання - скидаємо режим, щоб бот не зациклився
    context.user_data['mode'] = None
    await send_text(
        update,
        context,
        text="Генерирую резюме, подожди пару секунд..."
    )

    # Задаємо системний промпт
    chat_gpt.set_prompt(load_prompt('resume'))

    # Відправляємо відповіді та отримуємо результат
    resume_result = await chat_gpt.add_message(
        "\n\n".join(answers)
    )

    # Виводимо готове резюме та кнопку повернення
    await send_text_buttons(
        update,
        context,
        resume_result,
        buttons={'resume_finish': "Назад"}
    )

async def chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await chat_gpt.send_question("", update.effective_message.text)

    await send_text_buttons(
        update,
        context,
        response,
        {
            'random_finish': "Назад"
        }
    )


# Головний роутер для тексту
async def message_handler(update, context):
    mode = context.user_data.get('mode')

    if mode == 'gpt':
        await gpt_message(update, context)
    elif mode == 'talk':
        await talk_message(update, context)
    elif mode == 'quiz':
        await quiz_message(update, context)
    elif mode == 'resume':
        await resume_message(update, context)
    elif mode == 'chat':
        await chat_message(update, context)


async def voice_handler(update, context):

    if context.user_data.get('mode') != 'chat':
        return

    voice = update.effective_message.voice
    file = await context.bot.get_file(voice.file_id)

    await file.download_to_drive("voice.ogg")
    text = await analyze_audio("voice.ogg")

    answer = await chat_gpt.send_question(
        "",
        text
    )

    # Створюємо голосову відповідь
    audio_file = await generate_audio_response(answer)

    #Відправляємо голосову відповідь
    with open(audio_file, 'rb') as voice:
        await context.bot.send_voice(
            chat_id=update.effective_chat.id,
            voice=voice
    )

    await send_text_buttons(
        update,
        context,
        answer,
        {
            'random_finish': "Назад"
        }
    )


# ==================== НАЛАШТУВАННЯ БОТА ====================
chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

app.add_handler(
    MessageHandler(
        filters.VOICE,
        voice_handler
    )
)

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
for cmd in ['start', 'random', 'gpt', 'talk', 'quiz', 'resume', 'chat']:
    app.add_handler(CommandHandler(cmd, globals()[cmd]))

app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.|talk_finish|resume_finish'))
app.add_handler(CallbackQueryHandler(talk_button_handler, pattern='^talk_'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz'))
app.add_handler(CallbackQueryHandler(resume_message, pattern='^resume_finish$'))

app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()