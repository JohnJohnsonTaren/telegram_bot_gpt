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
        # Додати команду в меню можна так:
        # 'command': 'button text'

    })

# Функція рандомної кнопки
async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'random')
    prompt = load_prompt('random')
    response = await chat_gpt.send_question(prompt, 'Давай рандомний факт!')
    # await send_text(update, context, response)
    await send_text_buttons(
        update, context, response,
            {
                'random_finish': 'Закінчити',
                'random_one_more': 'Хочу ще факт'
            }
    )

async def random_buttons_handler(update: Update, context):
    query = update.callback_query.data
    if query == 'random_finish':
        await start(update, context)
    elif query == 'random_one_more':
        await random(update, context)

# Функція для обробки кнопки GPT
async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, 'gpt')
    await send_text(update, context, load_message('gpt'))
    #await send_text(update, context, "Напишіть своє запитання для ChatGPT:")
    #context.user_data['waiting_for_gpt'] = True

async def gpt_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_gpt'):
        return

    user_question = update.message.text
    response = await chat_gpt.send_question("", user_question)
    await send_text(update, context, response)
    context.user_data['waiting_for_gpt'] = False



chat_gpt = ChatGptService(credentials.ChatGPT_TOKEN)
app = ApplicationBuilder().token(credentials.BOT_TOKEN).build()

# Зареєструвати обробник команди можна так:
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('random', random))
app.add_handler(CommandHandler('gpt', gpt))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gpt_message))

# Зареєструвати обробник колбеку можна так:
app.add_handler(CallbackQueryHandler(random_buttons_handler, pattern='^random_.*'))
app.add_handler(CallbackQueryHandler(default_callback_handler))
app.run_polling()
