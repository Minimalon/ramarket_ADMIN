from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger

from core.database.queryDB import delete_saved_phones, get_saved_phones
from core.database.ramarket_shop.db_shop import create_excel_by_agent_id
from core.keyboards.inline import getKeyboard_currencies, getKeyboard_shop_functions, getKeyboard_delete_contacts
from core.utils import texts
from core.utils.callbackdata import DeleteContact, DeleteUsers
from core.oneC import api

api = api.Api()

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


async def select_to_delete_users(call: CallbackQuery, state: FSMContext, callback_data: DeleteUsers):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрали пользователя на удаление из базы 1С "{callback_data.id}"')
    data = await state.get_data()
    if not data.get('to_delete_1c'):
        to_delete_1c = callback_data.id
        await state.update_data(to_delete_1c=[callback_data.id])
    else:
        to_delete_1c = data.get('to_delete_1ñ')
        if callback_data.id in to_delete_1c:
            to_delete_1c.remove(callback_data.id)
        else:
            to_delete_1c.append(callback_data.id)
        await state.update_data(to_delete_1c=to_delete_1c)
    contacts = await get_saved_phones(chat_id=str(call.message.chat.id))
    await call.message.edit_text("Выберите пользователя на удаление", reply_markup=await getKeyboard_delete_contacts(contacts, to_delete_1c))


async def select_to_delete_contacts(call: CallbackQuery, state: FSMContext, callback_data: DeleteContact):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрали пользователя на удаление "{callback_data.phone}"')
    data = await state.get_data()
    if not data.get('to_delete'):
        to_delete = callback_data.phone
        await state.update_data(to_delete=[callback_data.phone])
    else:
        to_delete = data.get('to_delete')
        if callback_data.phone in to_delete:
            to_delete.remove(callback_data.phone)
        else:
            to_delete.append(callback_data.phone)
        await state.update_data(to_delete=to_delete)
    contacts = await get_saved_phones(chat_id=str(call.message.chat.id))
    await call.message.edit_text("Выберите пользователя на удаление", reply_markup=await getKeyboard_delete_contacts(contacts, to_delete))


async def delete_contacts(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    data = await state.get_data()
    log.info(f'Удалили пользователей "{data.get("to_delete")}"')
    await delete_saved_phones(str(call.message.chat.id), data.get('to_delete'))
    await state.update_data(to_delete=None)
    await call.message.edit_text(f'Пользователи удалены "<code>{",".join(data.get("to_delete"))}</code>"')


async def delete_users(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    data = await state.get_data()
    log.info(f'Удалили пользователей "{data.get("to_delete_1c")}"')
    response, all_users = await api.get_all_users()
    phones = [_['Телефон'] for _ in all_users if _['id'] in data.get('to_delete_1c')]
    await delete_saved_phones(str(call.message.chat.id), data.get('to_delete_1c'))
    await state.update_data(to_delete_1c=None)
    await call.message.edit_text(f'Пользователи удалены "<code>{",".join(data.get("to_delete_1c"))}</code>"')
