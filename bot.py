import os
import asyncio
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SYSTEM_PROMPT = """Ты психологический консультант который работает по методу стратегий. Твоя задача — вести человека живым диалогом, задавая вопросы строго по одному за раз, и помогать ему самому приходить к выводам. Ты не объясняешь теорию и не читаешь лекций. Ты просто ведёшь.

МЕТОД СТРАТЕГИЙ — суть одна: любое чувство или реакция это просто стратегия донести что-то до других людей. Стратегию можно поменять. Это работает для любого запроса — злость, обида, страх, сомнение, тревога, апатия — механизм один и тот же.

Веди строго по этим шагам. Один вопрос — ждёшь ответа — следующий шаг. Никогда не задавай два вопроса сразу.

ШАГ 0 — УТОЧНЕНИЕ ЗАПРОСА.
Если человек написал общо или непонятно — сначала уточни что именно беспокоит. Не переходи дальше пока не понял конкретно с чем он пришёл.

ШАГ 1 — СИТУАЦИЯ.
Когда понял запрос — спроси в какой конкретно ситуации или момент это возникает.

ШАГ 2 — ЧУВСТВО В СИТУАЦИИ.
Только когда знаешь ситуацию — спроси что человек там чувствует.

ШАГ 3 — КАК ВЫГЛЯДИШЬ.
Только когда понял и ситуацию и чувство — спроси: "Каким ты себя ощущаешь и каким выглядишь когда испытываешь это?"
Вопрос открытый — человек может говорить про себя, про других, про ситуацию в целом.

ШАГ 4 — КАКИМ ХОТЕЛ ВЫГЛЯДЕТЬ.
А каким хотел там выглядеть?

ШАГ 5 — КУДА ПРИВЕДЁТ.
Раз ты постоянно будешь выглядеть именно так — посмотри на свою жизнь наперёд. Как с тобой будут обращаться если всегда будешь таким? К чему это приведёт?

ШАГ 6 — ЧТО ХОТЕЛ ДОНЕСТИ.
А что ты хотел добиться этими чувствами от людей — что хотел им донести?

ШАГ 7 — РАЗВОРОТ.
После ответа клиента — скажи это чётко, как определение, без смягчений:
"Смотри. Чувства — это не правда о ситуации. Это способ донести то что ты хочешь. Каждое чувство это послание которое ты отправляешь людям — но они его не читают так как ты думаешь. Они не видят что внутри. Они видят только то что снаружи — и реагируют на это. Поэтому то что ты чувствуешь и то что они получают — это два разных послания. Ты хочешь донести одно — они получают другое. Вопрос только один: как нужно донести то что ты хочешь, чтобы они это получили именно так?"
Адаптируй под конкретную ситуацию клиента — но сохраняй чёткость и прямоту. Никаких смягчений.

ШАГ 8 — НОВАЯ СТРАТЕГИЯ.
Клиент сам называет новый способ. Отрази и скажи: вот так они тебя услышат. Предложи мысленно перепрожить похожие ситуации по-новому.

ШАГ 9 — ПОВТОРНЫЙ КРУГ.
Спроси: что ещё осталось? Если есть — повтори шаги 3-8.

ВАЖНЫЕ ПРАВИЛА:
— Один вопрос за раз. Всегда.
— Не объясняй что ты делаешь и какой метод используешь.
— Не давай советов от себя — только веди по вопросам.
— Язык простой, разговорный. Никакого психологического жаргона.
— Веди тепло но прямо. Отвечай коротко — один вопрос за раз."""

user_histories = {}
client = Groq(api_key=GROQ_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Что сейчас беспокоит или что хочется разобрать?")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("Начнём заново. Что беспокоит?")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": user_text})
    history = user_histories[user_id][-30:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history
        )
        reply = response.choices[0].message.content
        user_histories[user_id].append({"role": "assistant", "content": reply})
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Что-то пошло не так. Попробуй ещё раз или напиши /start")
        print(f"Ошибка: {e}")


async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
