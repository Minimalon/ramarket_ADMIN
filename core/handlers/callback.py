import asyncio

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger

from core.database.queryDB import delete_saved_phones, get_saved_phones, get_all_clients
from core.database.ramarket_shop.db_shop import create_excel_by_agent_id
from core.keyboards.inline import getKeyboard_currencies, getKeyboard_shop_functions, getKeyboard_delete_contacts, getKeyboard_delete_users, getKeyboard_filters_user_history_orders
from core.oneC import api
from core.oneC.oneC import get_employeeInfo
from core.utils import texts
from core.utils.callbackdata import DeleteContact, DeleteUsers
from core.utils.states import HistoryOrdersUser

api = api.Api()


async def select_currency(call: CallbackQuery):
    await call.message.edit_text('Выберите валюту', reply_markup=getKeyboard_currencies())


async def functions_shop(call: CallbackQuery):
    await call.message.edit_text('Выберите нужную операцию', reply_markup=getKeyboard_shop_functions())


async def select_filter_user_history_orders(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'История продаж одного пользователя')
    await call.message.edit_text('Выберите нужный вид истории', reply_markup=await getKeyboard_filters_user_history_orders())
    await state.set_state(HistoryOrdersUser.menu)


async def history_one_user_all_days(call: CallbackQuery, state: FSMContext, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'История продаж одного пользователя')
    data = await state.get_data()
    path = await create_excel_by_agent_id(data['user_id'], f"{'_'.join(data['agent_name'].split())}__all")
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
        to_delete_1c = data.get('to_delete_1c')
        if callback_data.id in to_delete_1c:
            to_delete_1c.remove(callback_data.id)
        else:
            to_delete_1c.append(callback_data.id)
        await state.update_data(to_delete_1c=to_delete_1c)
    response, contacts = await api.get_all_users()
    contacts = [_ for _ in contacts if _['Телефон'] not in ['79934055804', '79831358491']]
    await call.message.edit_text("Выберите пользователя на удаление", reply_markup=await getKeyboard_delete_users(contacts, to_delete_1c))


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
    await call.message.edit_text(f'Пользователи удалены "<code>{"|".join(data.get("to_delete"))}</code>"')


async def delete_users(call: CallbackQuery, state: FSMContext, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    data = await state.get_data()
    response, all_users = await api.get_all_users()
    phones = [_['Телефон'] for _ in all_users if _['id'] in data.get('to_delete_1c')]
    for client in await get_all_clients():
        if client.phones is None:
            continue
        for client_phone in client.phones.split(','):
            if client_phone in phones:
                employee = await get_employeeInfo(client_phone)
                await bot.send_message(client.chat_id, f'Данный сотрудник <code>{employee["Наименование"]}</code> с сотовым номером <code>{client_phone}</code> удалён из базы 1С')
                log.success(f'Оповестил админа "{client.chat_id}" об удалении "{employee["Наименование"]}" с сотовым номером "{client_phone}"')
    await state.update_data(to_delete_1c=None)
    for user_id in data.get('to_delete_1c'):
        await api.delete_user(user_id)
    employess_log = [[_['Телефон'], _['Наименование'], _['id']] for _ in all_users if _['id'] in data.get('to_delete_1c')]
    log.success(f'Удалил пользователей 1С {employess_log}')
    await call.message.edit_text(f'Пользователи удалены "<code>{"|".join(phones)}</code>"')


if __name__ == '__main__':
    a = asyncio.run(get_all_clients())
    print(a)
