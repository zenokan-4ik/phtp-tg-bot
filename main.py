import dotenv
import os

dotenv.load_dotenv()
TOKEN=os.getenv("TOKEN")

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from tools.Buttons import InlineButtons
from tools import messages as msgs

import admin_list as admins
import asyncio

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

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

@dp.message(RequestState.waiting_for_request)
async def process_request(msg: Message, state: FSMContext):
    user_request = msg.text
    
    # Process the request
    data = {
        'id': msg.from_user.id,
        'username': '@'+msg.from_user.username,
        'request': user_request
    }
    print(data['username'], ' | ', data['id'])
    
    successed_sends = 0
    for admin_id in admins.ADMINS_ID:
        if await send_msg_by_id(
            admin_id,
            f'<b>Новый запрос!!!!</b>\n\n\nПользователь: {data['username']}\nId пользователя: {data['id']}\nТекст запроса: {data['request']}'
        ):
            successed_sends += 1
    
    await msg.answer(f"Спасибо! Ваш запрос отправлен {successed_sends} {'участнику' if successed_sends%10 == 1 else 'участникам'}\nВаш запрос:\n{user_request}")
    await msg.answer(f"Если количество участников равно 0, то произошла ошибка. Можете обратиться к любому из участников напрямую с помоью кнопки 'Контакты'")
    
    await state.clear()
    
    await msg.answer("Чем еще могу помочь?", reply_markup=main_menu())

async def main() -> None:
    global bot
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())
    print('### Bot active! ###')