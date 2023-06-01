from aiogram.types import CallbackQuery

from core.keyboards.inline import getKeyboard_currencies, getKeyboard_shop_functions


async def select_currency(call: CallbackQuery):
    await call.message.edit_text('Выберите валюту', reply_markup=getKeyboard_currencies())


async def functions_shop(call: CallbackQuery):
    await call.message.edit_text('Выберите нужную операцию', reply_markup=getKeyboard_shop_functions())
