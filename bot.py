from asyncio import create_task, run
from aiohttp import ClientSession
from data import Subscription, get_user, connect_database
from time import strftime
from base64 import b64decode
from config import TOKEN, BOT_PROXY, HEADERS, API_ENABLED, API_DISPLAY, THRONE_VER, HAPP_VER, INCY_VER
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InaccessibleMessage, BufferedInputFile
from aiogram.filters import Command, CommandObject
from aiogram.client.session.aiohttp import AiohttpSession

if BOT_PROXY == None:
    bot = Bot(TOKEN)
else:
    session = AiohttpSession(proxy=BOT_PROXY)
    bot = Bot(TOKEN, session=session)

dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(msg: Message):
    api_text = ""
    if API_ENABLED:
        api_text = "<b>🔧 API</b>\n - Информация о API доступна по команде /api"
    await msg.reply(f"""ℹ️ <b>FakeHWBot</b>

<b>🔗 Подписки</b>
 - Подписки добавляются в ваш клиент
 - Чтобы экспортировать добавленные: нажмите на кнопку с нужным номером в /subs
 - Дополнительная информация указана в той же команде

<b>❓ Использование бота</b>
1. Добавление подписок: <code>/add ССЫЛКА КЛИЕНТ</code>
 - Доступные клиенты: <code>{"</code>, <code>".join(HEADERS.keys())}</code> (либо в /clients)
2. Удаление подписок (если нужно): <code>/remove НОМЕР</code>
3. Обновление подписок: /subs

<b>⚙️ Информация о клиентах</b>
 - Информация о клиентах доступна по команде /clients

{api_text}""", parse_mode="HTML")

@dp.message(Command("clients"))
async def hwid_command(msg: Message):
    await msg.reply(f"""<b>⚙️ Текущие клиенты</b>
1. Throne {THRONE_VER} (ветка singbox): <pre>hwid={HEADERS['singbox']['x-hwid']},os={HEADERS['singbox']['x-device-os']},osVersion={HEADERS['singbox']['x-ver-os']},model={HEADERS['singbox']['x-device-model']}</pre>
2. Happ {HAPP_VER}: <pre>Locale: {HEADERS['happ']['X-Device-Locale']}
OS: {HEADERS['happ']['X-Device-Os']} (version: {HEADERS['happ']['X-Ver-Os']})
Device Model: {HEADERS['happ']['X-Device-Model']}
HWID: {HEADERS['happ']['X-Hwid']}
</pre>
3. Incy {INCY_VER}: <pre>Locale: {HEADERS['incy']['x-device-locale']}
OS: {HEADERS['incy']['x-device-os']} (version: {HEADERS['incy']['x-ver-os']})
Device Model: {HEADERS['incy']['x-device-model']}
HWID: {HEADERS['incy']['x-hwid']}
Client: {HEADERS['incy']['x-client']} {HEADERS['incy']['x-app-version']}</pre>""", parse_mode="HTML")

@dp.message(Command("api"))
async def api_command(msg: Message):
    if API_ENABLED == False:
        return await msg.reply("❌ <b>API выключено</b>", parse_mode="HTML")
    
    if msg.from_user == None: return
    user = await get_user(msg.from_user.id)
    
    await msg.reply(f"🔧 <b>API</b>\n - Ваш токен: <code>{user.token}</code>\nДокументация: <code>{API_DISPLAY}/docs</code>", parse_mode="HTML")

@dp.message(Command("subs"))
async def subs_command(msg: Message):
    if msg.from_user == None: return
    user = await get_user(msg.from_user.id)
    
    subs_text: list[str] = []
    keyboard_buttons: list[list[InlineKeyboardButton]] = []
    for index, sub in enumerate(user.subscriptions):
        display_index = f"{index + 1}"
        subs_text.append(f"{display_index}. {sub}")
        keyboard_buttons.append([InlineKeyboardButton(text=display_index, callback_data=f"gp:{index}")])

    keyboard: InlineKeyboardMarkup | None = None
    if len(keyboard_buttons) > 0:
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
    api_text = ""
    if API_ENABLED == True:
        api_text = f"\n\n🔗 <b>Добавление в клиент</b>\n - Чтобы не добавлять файл каждый раз, подписку можно добавить по ссылке ниже\n - ⚠️ <b>ВАЖНО!</b> Замените номер в ссылке на номер подписки\n<code>{API_DISPLAY}/subs/{user.token}/НОМЕР</code>"

    await msg.reply(f"📃 <b>Ваши подписки</b><pre>{"\n".join(subs_text)}</pre>\nЧтобы экспортировать их в файл нажмите на кнопку с нужным номером{api_text}", parse_mode="HTML", reply_markup=keyboard)

@dp.message(Command("add"))
async def add_command(msg: Message, command: CommandObject):
    if msg.from_user == None: return
    
    args = []
    if command.args != None:
        args = command.args.split(" ")
    
    if len(args) < 2:
        return await msg.reply("❌ <b>Неправильное использование /add:</b> не указаны подписка и клиент\n - Пример: <code>/add ПОДПИСКА КЛИЕНТ</code>\n - Использование команд описано в /start", parse_mode="HTML")
    
    link = args[0]
    if link.isascii() == False:
        return await msg.reply("❌ <b>Неправильное использование /add:</b> присутствуют не ASCII символы", parse_mode="HTML")
    if len(link) > 64:
        return await msg.reply("❌ <b>Неправильное использование /add:</b> максимум символов в подписке - 64", parse_mode="HTML")
    
    header = args[1]
    if (header in HEADERS) == False:
        return await msg.reply("❌ <b>Неправильное использование /add:</b> клиент не найден\n - Доступные клиенты описаны в /start", parse_mode="HTML")
    
    user = await get_user(msg.from_user.id)
    if len(user.subscriptions) >= 5:
        return await msg.reply("❌ <b>Неправильное использование /add:</b> максимум подписок на аккаунт - 5", parse_mode="HTML")
    
    user.subscriptions.append(Subscription(link, header))
    await user.save()
    await msg.reply("✅ <b>Подписка сохранена</b>\n - Обновить её можно в /subs", parse_mode="HTML")

@dp.message(Command("remove"))
async def remove_command(msg: Message, command: CommandObject):
    if msg.from_user == None: return
    
    if command.args == None:
        return await msg.reply("❌ <b>Неправильное использование /remove:</b> не указан номер\n - Пример: <code>/remove НОМЕР</code>", parse_mode="HTML")
    args = command.args.split(" ")
    
    try:
        index = int(args[0]) - 1
    except ValueError:
        return await msg.reply("❌ <b>Неправильное использование /remove:</b> номер не число", parse_mode="HTML")
    
    user = await get_user(msg.from_user.id)
    if index < 0 or index + 1 > len(user.subscriptions):
        return await msg.reply("❌ <b>Неправильное использование /remove:</b> номер не найден", parse_mode="HTML")
    
    user.subscriptions.pop(index)
    await user.save()
    await msg.reply("✅ <b>Подписка удалена</b>", parse_mode="HTML")

@dp.callback_query()
async def on_callback_query(callback: CallbackQuery):
    message = callback.message
    if message == None or callback.data == None or isinstance(message, InaccessibleMessage): return
    
    if callback.data.startswith("gp"):
        index = int(callback.data[3:]) # gp:index
        user = await get_user(callback.from_user.id)
        if index < 0 or index + 1 > len(user.subscriptions):
            return
        sub = user.subscriptions[index]
        
        await message.delete()

        try:
            async with ClientSession() as session:
                response = await sub.send_request(session)
                text = await response.text()
        except Exception:
            return await callback.answer("Не удалось обновить подписку", show_alert=True)
        
        buf: bytes
        if sub.headers == "singbox":
            buf = b64decode(text)
        elif sub.headers == "happ" or sub.headers == "incy":
            buf = text.encode()
        else:
            return await callback.answer("Клиент не найден", show_alert=True)
        
        filename = f"subexport ({strftime("%m-%d %H.%M.%S")}).txt"
        return await bot.send_document(message.chat.id, BufferedInputFile(buf, filename))

async def main():
    await connect_database()
    
    if API_ENABLED:
        import api
        create_task(api.start())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    run(main())