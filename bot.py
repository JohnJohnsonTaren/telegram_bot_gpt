from asyncio import tasks

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, ContextTypes, CommandHandler, MessageHandler, filters

from gpt import ChatGptService
from util import (load_message, send_text, send_image, show_main_menu,
                  default_callback_handler, load_prompt, send_text_buttons)

import credentials


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = load_message('main')
    await send_image(update, context, 'main')
    await send_text(update, context, text)
    await show_main_menu(update, context, {
        'start': 'Головне меню',
        'random': 'Дізнатися випадковий цікавий факт 🧠',
        'gpt': 'Задати питання чату GPT 🤖',
        'talk': 'Поговорити з відомою особистістю 👤',
        'quiz': 'Взяти участь у квізі ❓'
    })


# Функція рандомної кнопки
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'random')
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, 'Давай рандомний факт!')
    await send_text_buttons(
        update, context, response,
        {
            'random_finish': 'Закінчити',
            'random_one_more': 'Хочу ще факт'
        }
    )


# Диспетчер натискання кнопок
async def random_buttons_handler(update: Update, context):
    query = update.callback_query.data

    if query == 'random_finish':
        await start(update, context)
        return
    elif query == 'random_one_more':
        await random(update, context)
        return

    if query == 'talk_finish':
        context.user_data['waiting_for_talk'] = False
        context.user_data['waiting_for_gpt'] = False
        await start(update, context)
        return

    prompts = {
        '1': "Ти Курт Кобейн. Відповідай від його імені.",
        '2': "Ти Єлизавета II. Відповідай від її імені.",
        '3': "Ти Джон Толкін. Відповідай від його імені.",
        '4': "Ти Фрідріх Ніцше. Відповідай від його імені.",
        '5': "Ти Стівен Гокінг. Відповідай від його імені."
    }

    if query not in prompts:
        return

    context.user_data['talk_prompt'] = prompts[query]
    context.user_data['waiting_for_talk'] = True
    context.user_data['waiting_for_gpt'] = False

    # Додаємо кнопку "Закінчити" вже на етапі запрошення до діалогу
    await send_text_buttons(
        update,
        context,
        "Напишіть повідомлення для співрозмовника.",
        {
            'talk_finish': 'Закінчити'
        }
    )


# Функція для обробки кнопки GPT
async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))
    context.user_data['waiting_for_gpt'] = True
    context.user_data['waiting_for_talk'] = False


# Об'єднуємо MessageHandler для уникнення конфліктів
async def message_handler(update, context):
    if context.user_data.get('waiting_for_gpt'):
        user_question = update.message.text
        response = await chat_gpt.send_question("", user_question)
        await send_text(update, context, response)
        context.user_data['waiting_for_gpt'] = False
        return

    if context.user_data.get('waiting_for_talk'):
        user_message = update.message.text
        prompt = context.user_data['talk_prompt']
        response = await chat_gpt.send_question(prompt, user_message)

        await send_text_buttons(
            update, context, response,
            {
                'talk_finish': 'Закінчити'
            }
        )
        return


# Функція діалогу
async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'talk')
    await send_text(update, context, load_message('talk'))

    await send_text_buttons(
        update, context, "Оберіть Співрозмовника ",
        {
            '1': 'Курт Кобейн',
            '2': 'Єлизавета II',
            '3': 'Джон Толкін',
            '4': 'Фрідріх Ніцше',
            '5': 'Стівен Гокінг'
        }
    )


chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник повідомлень (тільки один універсальний!)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

# Зареєструвати обробники команд
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(CommandHandler('talk', talk))

# Зареєструвати обробники колбеків
app.add_handler(CallbackQueryHandler(random_buttons_handler))
app.add_handler(CallbackQueryHandler(default_callback_handler))

app.run_polling()