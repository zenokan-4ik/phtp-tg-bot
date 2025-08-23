from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class InlineButtons:
    def __init__(self, namesList: list[str], callbackList: list[str]):
        self.namesList = namesList
        self.callbackList = callbackList
        self.result = self._create_keyboard()
    
    def _create_keyboard(self) -> InlineKeyboardMarkup:
        buttons = []
        for name, callback in zip(self.namesList, self.callbackList):
            buttons.append([InlineKeyboardButton(text=name, callback_data=callback)])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    def __call__(self) -> InlineKeyboardMarkup:
        return self.result