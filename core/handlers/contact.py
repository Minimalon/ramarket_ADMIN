from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from core.database.queryDB import save_phone, get_client_info
from core.keyboards.inline import getKeyboard_contact_false, getKeyboard_contact_true
from core.oneC import oneC
from core.utils import texts
from core.utils.callbackdata import SavedContact
from core.utils.states import Contact


async def get_contact(message: Message, state: FSMContext):
    log = logger.bind(chat_id=message.chat.id, first_name=message.chat.first_name)
    phone = texts.phone(message.contact.phone_number)
    employee = await oneC.get_employeeInfo(phone)
    if employee:
        await state.set_state(Contact.menu)
        await save_phone(str(message.chat.id), texts.phone(message.contact.phone_number))
        shops = [[i['Магазин'], i['idМагазин']] for i in employee["Магазины"]]
        await state.update_data(shops=shops, user_id=employee['id'], agent_name=employee['Наименование'])
        log.info('Сотрудник найден в базе 1С')
        client_info = await get_client_info(message.chat.id)
        admin_info = await oneC.get_employeeInfo(client_info.phone_number)
        text = await texts.employee_true(employee, phone, admin_info, client_info.admin)
        await message.answer(text, reply_markup=getKeyboard_contact_true(superadmin=client_info.admin, employee_info=employee, admin_info=admin_info))
    else:
        log.error('Сотрудник не найден в базе 1С')
        text = f"Данный контакт '<code>{phone}</code>' не зарегистрирован"
        await message.answer(text, reply_markup=getKeyboard_contact_false(phone))


async def get_saved_contact(call: CallbackQuery, state: FSMContext, callback_data: SavedContact):
    log = logger.bind(chat_id=call.message.chat.id, first_name=call.message.chat.first_name)
    phone = texts.phone(callback_data.phone)
    employee = await oneC.get_employeeInfo(phone)
    if employee:
        await state.set_state(Contact.menu)
        shops = [[i['Магазин'], i['idМагазин']] for i in employee["Магазины"]]
        await state.update_data(shops=shops, user_id=employee['id'], agent_name=employee['Наименование'])
        log.info('Сотрудник найден в базе 1С')
        client_info = await get_client_info(call.message.chat.id)
        admin_info = await oneC.get_employeeInfo(client_info.phone_number)
        text = await texts.employee_true(employee, phone, admin_info, client_info.admin)
        await call.message.edit_text(text, reply_markup=getKeyboard_contact_true(superadmin=client_info.admin, employee_info=employee, admin_info=admin_info))
    else:
        log.error('Сотрудник не найден в базе 1С')
        text = f"Данный контакт '<code>{phone}</code>' не зарегистрирован"
        await call.message.answer(text, reply_markup=getKeyboard_contact_false(phone))
