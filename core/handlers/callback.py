from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger

from core.database.ramarket_shop.db_shop import create_excel_by_agent_id
from core.keyboards.inline import getKeyboard_currencies, getKeyboard_shop_functions
from core.utils import texts


async def select_currency(call: CallbackQuery):
    await call.message.edit_text('Выберите валюту', reply_markup=getKeyboard_currencies())


async def functions_shop(call: CallbackQuery):
    await call.message.edit_text('Выберите нужную операцию', reply_markup=getKeyboard_shop_functions())


async def historyOneUser(call: CallbackQuery, state: FSMContext, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'История продаж одного пользователя')
    data = await state.get_data()
    path = await create_excel_by_agent_id(data['user_id'], data['agent_name'])
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
        await state.clear()
    else:
        await call.message.answer(texts.error_head + "Данный сотрудник еще не делал продаж")
        await call.answer()
