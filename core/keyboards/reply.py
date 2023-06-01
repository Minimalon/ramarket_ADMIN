from aiogram.utils.keyboard import ReplyKeyboardBuilder

from core.database.queryDB import get_saved_phones
from core.oneC.oneC import Api
from core.utils.callbackdata import SavedContact

api = Api()


def getKeyboard_registration():
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text='Регистрация', request_contact=True)
    keyboard.adjust(1)
    return keyboard.as_markup(one_time_keyboard=True)



