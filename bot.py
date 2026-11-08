from asyncio import create_task, run
from data import Subscription, get_user, connect_database
from time import strftime
from base64 import b64decode
from requests import RequestException
from config import TOKEN, BOT_PROXY, HEADERS, THRONE_VER, HAPP_VER, API_ENABLED, API_DISPLAY
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
    if msg.from_user == None or msg.from_user.id == None: return
    user = await get_user(msg.from_user.id)
    
    subs_text = []
    keyboard_buttons: list[list[InlineKeyboardButton]] = []
    for index, sub in enumerate(user.subscriptions):
        display_index = f"{index + 1}"
        subs_text.append(f"{display_index}. {sub}")
        keyboard_buttons.append([InlineKeyboardButton(text=display_index, callback_data=f"gp:{index}")])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    api_text = ""
    if API_ENABLED:
        api_text = "<b>📨 API</b>\nTo get your api-url (for example subscription updating) use <code>/api</code>\n"
    await msg.reply(f"""<b>📃 Your subscriptions</b>
<pre>{"\n".join(subs_text)}</pre>

To modify subscriptions use:
1. <code>/add SUB_URL {"/".join(HEADERS.keys())}</code>
2. <code>/remove INDEX</code>

{api_text}
<b>🔖 Current HWID</b>
1. Throne {THRONE_VER} (/singbox): <pre>hwid={HEADERS['singbox']['x-hwid']},os={HEADERS['singbox']['x-device-os']},osVersion={HEADERS['singbox']['x-ver-os']},model={HEADERS['singbox']['x-device-model']}
</pre>
2. Happ: <pre>Locale: {HEADERS['happ']['X-Device-Locale']}
OS: {HEADERS['happ']['X-Device-Os']} (version: {HEADERS['happ']['X-Ver-Os']})
Device Model: {HEADERS['happ']['X-Device-Model']}
HWID: {HEADERS['happ']['X-Hwid']}
Happ version: {HAPP_VER}
</pre>
3. Incy: <pre>Locale: {HEADERS['incy']['x-device-locale']}
OS: {HEADERS['incy']['x-device-os']} (version: {HEADERS['incy']['x-ver-os']})
Device Model: {HEADERS['incy']['x-device-model']}
HWID: {HEADERS['incy']['x-hwid']}
Client: {HEADERS['incy']['x-client']} {HEADERS['incy']['x-app-version']}</pre>""", reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("api"))
async def api_command(msg: Message):
    if API_ENABLED == False:
        return await msg.reply("API Disabled")
    
    if msg.from_user == None or msg.from_user.id == None: return
    user = await get_user(msg.from_user.id)
    
    await msg.reply(f"Your API token: <code>{user.token}</code>\nExample: <code>{API_DISPLAY}/user/TOKEN/subs/0</code>\nDocs available here: {API_DISPLAY}/redoc", parse_mode="HTML")

@dp.message(Command("add"))
async def add_command(msg: Message, command: CommandObject):
    if msg.from_user == None or msg.from_user.id == None: return
    
    if command.args == None:
        return await msg.reply(f"Invalid usage of /add: no sub_url argument\nExample: /add <sub_url> <{"/".join(HEADERS.keys())}>")
    args = command.args.split(" ")
    
    if len(args) < 2:
        return await msg.reply(f"Invalid usage of /add: no headers argument\nExample: /add <sub_url> <{"/".join(HEADERS.keys())}>")
    
    link = args[0]
    if link.isascii() == False:
        return await msg.reply("Invalid usage of /add: non-ascii characters")
    if len(link) > 64:
        return await msg.reply("Invalid usage of /add: maximum length of sub_url reached")
    
    header = args[1]
    if header in HEADERS == False:
        return await msg.reply(f"Invalid usage of /add: invalid header\nExample headers: {" or ".join(HEADERS.keys())}")
    
    user = await get_user(msg.from_user.id)
    if len(user.subscriptions) > 5:
        return await msg.reply("Invalid usage of /add: maximum subscriptions count reached")
    
    user.subscriptions.append(Subscription(link, header))
    await user.save()
    await msg.reply("Saved!")

@dp.message(Command("remove"))
async def remove_command(msg: Message, command: CommandObject):
    if msg.from_user == None or msg.from_user.id == None: return
    
    if command.args == None:
        return await msg.reply("Invalid usage of /remove: no index argument\nExample: /remove <index>")
    args = command.args.split(" ")
    
    try:
        index = int(args[0]) - 1
    except ValueError:
        return await msg.reply("Invalid usage of /remove: index is not a number")
    
    user = await get_user(msg.from_user.id)
    if index < 0 or index + 1 > len(user.subscriptions):
        return await msg.reply("Invalid usage of /remove: index is outside your subscriptions")
    
    user.subscriptions.pop(index)
    await user.save()
    await msg.reply("Removed!")

@dp.callback_query()
async def on_callback_query(callback: CallbackQuery):
    message = callback.message
    if message == None or \
        callback.from_user == None or \
            callback.from_user.id == None or \
                callback.data == None or \
                    isinstance(message, InaccessibleMessage): return
    
    if callback.data.startswith("gp"):
        index = int(callback.data[3:]) # gp:index
        user = await get_user(callback.from_user.id)
        if index < 0 or index + 1 > len(user.subscriptions):
            return
        sub = user.subscriptions[index]
        
        await message.delete()

        try:
            res = sub.send_request()
        except RequestException:
            return await callback.answer("Failed to get profiles", show_alert=True)
        
        buf: bytes
        if sub.headers == "singbox":
            buf = b64decode(res.content)
        elif sub.headers == "happ" or sub.headers == "incy":
            buf = res.text.encode()
        else:
            return await callback.answer("Invalid headers", show_alert=True)
        
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