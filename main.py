import dotenv
import os

dotenv.load_dotenv()
TOKEN=os.getenv("TOKEN")

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from tools.Buttons import InlineButtons
from tools import messages as msgs
from tools.api import Api

from config import API_URL

import admin_list as admins
import asyncio

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
api = Api(API_URL)


main_menu = InlineButtons(
    namesList=[
        'Контакты', 'Отправить заявку'
    ],
    callbackList=[
        'contacts', 'request'
    ],
)

class RequestState(StatesGroup):
    waiting_for_request = State()
    
async def send_msg_by_id(user_id: int, text: str, parse_mode: ParseMode = ParseMode.HTML):
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        print(f"Failed to send message to user {user_id}: {e}")
        return False

async def send_msg(msg: Message, text: str):
    await msg.answer(
        text=text,
        parse_mode=ParseMode.HTML
    )

@dp.message(CommandStart())
async def start_command(msg: Message):
    await msg.answer(
        f'Hello!!',
        reply_markup=main_menu()
    )
    
@dp.callback_query()
async def process_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()
    print(callback_query.data, ' answered')
    match callback_query.data:
        case 'contacts': 
            await send_msg(callback_query.message, msgs.CONTACTS)
        case 'request':
            await send_msg(callback_query.message, msgs.REQUEST)
            await state.set_state(RequestState.waiting_for_request)

from io import BytesIO
import aiohttp

@dp.message(RequestState.waiting_for_request)
async def process_request(msg: Message, state: FSMContext):
    user_request = msg.text or msg.caption or ""
    
    # Process the request
    data = {
        'id': msg.from_user.id,
        'username': '@' + msg.from_user.username if msg.from_user.username else str(msg.from_user.id),
        'request': user_request
    }

    files = {}
    photo_data = []

    if msg.photo:
        photos = msg.photo
        largest_photo = photos[-1]
        file_info = await bot.get_file(largest_photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        photo_data.append({
            'file_id': largest_photo.file_id,
            'bytes': downloaded_file.read()
        })
        
        downloaded_file.seek(0)
        files['photo'] = ('photo.jpg', downloaded_file)

    resp = api.post('addrequest/', data={
        'tg_id': data['id'],
        'username': data['username'],
        'request': data['request'],
    }, files=files)

    print('## ', resp)
    print(data['username'], ' | ', data['id'])

    successed_sends = 0
    admin_message_text = f'<b>Новый запрос!!!!</b>\n\n\nПользователь: {data["username"]}\nID пользователя: {data["id"]}\nТекст запроса: {data["request"]}'

    for admin_id in admins.ADMINS_ID:
        try:
            if photo_data:
                await bot.send_photo(
                    admin_id,
                    photo=photo_data[0]['bytes'],
                    caption=admin_message_text,
                    parse_mode='HTML'
                )
            else:
                await bot.send_message(
                    admin_id,
                    admin_message_text,
                    parse_mode='HTML'
                )
            successed_sends += 1
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")

    await msg.answer(f"Спасибо! Ваш запрос отправлен {successed_sends} {'участнику' if successed_sends == 1 else 'участникам'}\nВаш запрос:\n{user_request}")
    
    if successed_sends == 0:
        await msg.answer("Если количество участников равно 0, то произошла ошибка. Можете обратиться к любому из участников напрямую с помощью кнопки 'Контакты'")
    
    await state.clear()
    await msg.answer("Чем еще могу помочь?", reply_markup=main_menu())

async def main() -> None:
    global bot
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
    print('### Bot active! ###')