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
    send_text_buttons)

import credentials


# ==================== СТАРТ ТА ГОЛОВНІ РЕЖИМИ ====================
# Кнопки для головного меню /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'main')
    await send_text(update, context, load_message('main'))

    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
    })

# Кнопки для /random
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# Діалог з /gpt
async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))

    context.user_data['mode'] = 'gpt'

# Кнопки для /talk
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await send_image(update, context, 'quiz')
    context.user_data['mode'] = 'quiz'

    await send_text_buttons(
        update,
        context,
        load_message('quiz'),
        buttons={
                    'quiz_prog': "Програмування Python 🐍",
                    'quiz_math': "Математичні теорії 📐",
                    'quiz_biology': "Біологія 🌿"
                }
    )


# ==================== ДИСПЕТЧЕР КНОПОК ====================
# Логіка натискання кнопок у /random
async def random_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_random = update.callback_query.data

    # Логіка рандому
    if query_random in ['random_finish', 'talk_finish']:
        await start(update, context)
    elif query_random == 'random_one_more':
        await random(update, context)

# Логіка натискання кнопок у /talk
async def talk_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_talk = update.callback_query.data

    if query_talk in ['talk_cobain', 'talk_queen', 'talk_tolkien', 'talk_nietzsche', 'talk_hawking']:
        context.user_data['talk_prompt'] = query_talk
        await send_text(update, context, "Напишіть повідомлення для співрозмовника.")

# Логіка натискання кнопок у /quiz
async def quiz_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_quiz = update.callback_query.data

    response = await chat_gpt.send_question(load_prompt('quiz'), update.callback_query.data)
    await send_text(update, context, response)


# ==================== ОБРОБКА ПОВІДОМЛЕНЬ ====================
async def gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await chat_gpt.send_question("", update.message.text)
    await send_text(update, context, response)

async def talk_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = context.user_data.get('talk_prompt')
    response = await chat_gpt.send_question(load_prompt(prompt), update.message.text)
    await send_text_buttons(update, context, response, {'random_finish': 'Закінчити'})

async def quiz_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_ans = update.message.text.strip().lower()
    correct_ans = context.user_data.get('quiz', '').strip().lower()

    if user_ans == correct_ans:
        reply = "Правильно!"
    else:
        original = context.user_data.get('quiz', '')
        reply = f"Неправильно! Правильна відповідь - {original}"

    context.user_data['waiting_for_quiz'] = False

    await send_text_buttons(
        update,
        context,
        reply,
        buttons={
            'quiz_more': "Наступне запитання",
            'quiz_finish': "Закінчити"
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


# ==================== НАЛАШТУВАННЯ БОТА ====================

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
for cmd in ['start', 'random', 'gpt', 'talk', 'quiz']:
    app.add_handler(CommandHandler(cmd, globals()[cmd]))

app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_'))
app.add_handler(CallbackQueryHandler(talk_button_handler, pattern='^talk_'))
app.add_handler(CallbackQueryHandler(quiz_buttons_handler, pattern='^quiz_'))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()