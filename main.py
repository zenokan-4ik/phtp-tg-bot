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

from aiogram.types import BufferedInputFile
from io import BytesIO
from aiogram.types import InputMediaPhoto

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

from aiogram.types import InputMediaPhoto
import asyncio

# Dictionary to track media groups
media_groups = {}

from aiogram.types import InputMediaPhoto
import asyncio

# Dictionary to track media groups
media_groups = {}

# Add this at the top of your file with other global variables
processed_media_groups = set()

@dp.message(RequestState.waiting_for_request)
async def process_request(msg: Message, state: FSMContext):
    # Skip processing if this is a media group message without caption/text
    if msg.media_group_id and not (msg.text or msg.caption):
        if msg.media_group_id in processed_media_groups:
            return
        # Mark this media group as processed
        processed_media_groups.add(msg.media_group_id)
        # Set a timer to remove the media group ID after a while
        asyncio.create_task(remove_media_group_id(msg.media_group_id))
        return

    user_request = msg.text or msg.caption
    data = {
        'id': msg.from_user.id,
        'username': '@' + msg.from_user.username if msg.from_user.username else str(msg.from_user.id),
        'request': user_request
    }

    files = {}
    photo_bytes = None

    # Handle only the highest resolution photo
    if msg.photo:
        # Get the highest resolution photo (last in the array)
        largest_photo = msg.photo[-1]
        file_info = await bot.get_file(largest_photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        photo_bytes = downloaded_file.read()
        
        # Reset file pointer for API upload
        downloaded_file.seek(0)
        files['photo'] = ('photo.jpg', downloaded_file)
        
        # If this is part of a media group, mark it as processed
        if msg.media_group_id:
            processed_media_groups.add(msg.media_group_id)
            # Set a timer to remove the media group ID after a while
            asyncio.create_task(remove_media_group_id(msg.media_group_id))

    # API request
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
            if photo_bytes:
                # Create BufferedInputFile from bytes
                input_file = BufferedInputFile(photo_bytes, filename='photo.jpg')
                await bot.send_photo(
                    admin_id,
                    photo=input_file,
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

# Add this helper function to clean up media group IDs
async def remove_media_group_id(media_group_id):
    await asyncio.sleep(30)  # Wait 30 seconds
    if media_group_id in processed_media_groups:
        processed_media_groups.remove(media_group_id)

async def main() -> None:
    global bot
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
    print('### Bot active! ###')