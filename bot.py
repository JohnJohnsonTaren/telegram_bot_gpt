from tkinter import dialog

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)

import credentials


# ==================== СТАРТ ТА ГОЛОВНІ РЕЖИМИ ====================

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


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'random')
    response = await chat_gpt.send_question(load_prompt('random'), 'Давай рандомний факт!')
    await send_text_buttons(update, context, response, {
        'random_finish': 'Закінчити',
        'random_one_more': 'Хочу ще факт'
    })


async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))
    context.user_data.update({'waiting_for_gpt': True, 'waiting_for_talk': False, 'waiting_for_quiz': False})


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'talk')
    await send_text_buttons(update, context, load_message('talk'), {
        'Cobain': 'Курт Кобейн',
        'Elizabeth': 'Єлизавета II',
        'Tolkien': 'Джон Толкін',
        'Nietzsche': 'Фрідріх Ніцше',
        'Hawking': 'Стівен Гокінг'
    })


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialog.mode = 'quiz'
    await send_image(update, context, 'quiz')
    await send_text_buttons(update, context, load_message('quiz'), {
        'quiz_prog': "Програмування Python 🐍",
        'quiz_math': "Математичні теорії 📐",
        'quiz_biology': "Біологія 🌿",
        'quiz_more': "Наявна тема"
    })


# ==================== ДИСПЕТЧЕР КНОПОК ====================

async def random_buttons_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data

    # Логіка рандому
    if query in ['random_finish', 'talk_finish']:
        context.user_data.update({'waiting_for_talk': False, 'waiting_for_gpt': False, 'waiting_for_quiz': False})
        await start(update, context)
        return
    elif query == 'random_one_more':
        await random(update, context)
        return



    # Логіка генерації питання квізу
    if query in ['quiz_prog', 'quiz_math', 'quiz_biology', 'quiz_more']:

        if query != 'quiz_more':
            context.user_data['quiz_topic'] = query

        topic = context.user_data['quiz_topic']

        topics = {
            'quiz_prog': 'Python',
            'quiz_math': 'теорія алгоритмів, теорія множин та математичний аналіз',
            'quiz_biology': 'біологія'
        }

        prompt = f"""
        Згенеруй ОДНЕ питання на тему {topics[topic]}.

        Поверни відповідь строго у форматі:

        ПИТАННЯ: ...
        ВІДПОВІДЬ: ...

        Відповідь має складатися максимум з кількох слів.
        Не використовуй числа у відповіді.
        """

        response = await chat_gpt.send_question(
            prompt,
            "Створи питання"
        )

        lines = response.split('\n')

        question = ""
        answer = ""

        for line in lines:
            if line.startswith("ПИТАННЯ:"):
                question = line.replace("ПИТАННЯ:", "").strip()

            if line.startswith("ВІДПОВІДЬ:"):
                answer = line.replace("ВІДПОВІДЬ:", "").strip()

        context.user_data['quiz_answer'] = answer.lower()

        context.user_data.update({
            'waiting_for_quiz': True,
            'waiting_for_gpt': False,
            'waiting_for_talk': False
        })

        await send_text(update, context, question)
        return



    # Логіка вибору співрозмовника
    prompts = {
        'Cobain': "Ти Курт Кобейн. Відповідай від його імені.",
        'Elizabeth': "Ти Єлизавета II. Відповідай від її імені.",
        'Tolkien': "Ти Джон Толкін. Відповідай від його імені.",
        'Nietzsche': "Ти Фрідріх Ніцше. Відповідай від його імені.",
        'Hawking': "Ти Стівен Гокінг. Відповідай від його імені."
    }
    if query in prompts:
        context.user_data.update({'talk_prompt': prompts[query], 'waiting_for_talk': True, 'waiting_for_gpt': False,
                                  'waiting_for_quiz': False})
        await send_text(update, context, "Напишіть повідомлення для співрозмовника.")


# ==================== ОБРОБКА ПОВІДОМЛЕНЬ ====================

async def gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await chat_gpt.send_question("", update.message.text)
    await send_text(update, context, response)


async def talk_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = await chat_gpt.send_question(context.user_data['talk_prompt'], update.message.text)
    await send_text_buttons(update, context, response, {'talk_finish': 'Закінчити'})


async def quiz_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_ans = update.message.text.strip().lower()
    correct_ans = context.user_data.get('quiz_answer', '')

    reply = "Правильно!" if user_ans == correct_ans or user_ans in correct_ans else f"Неправильно! Правильна відповідь - {context.user_data.get('quiz_answer')}"

    await send_text_buttons(update, context, reply, {'quiz_more': "Наступне запитання", 'talk_finish': "Закінчити"})


# Головний роутер для тексту
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_gpt'):
        await gpt_message(update, context)
    elif context.user_data.get('waiting_for_talk'):
        await talk_message(update, context)
    elif context.user_data.get('waiting_for_quiz'):
        await quiz_message(update, context)


# ==================== НАЛАШТУВАННЯ БОТА ====================

chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
for cmd in ['start', 'random', 'gpt', 'talk', 'quiz']:
    app.add_handler(CommandHandler(cmd, globals()[cmd]))

app.add_handler(CallbackQueryHandler(random_buttons_handler))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()