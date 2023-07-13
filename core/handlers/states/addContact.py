from loguru import logger

from aiogram.fsm.context import FSMContext
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.oneC import oneC
from core.keyboards.inline import getKeyboard_contact_true, getKeyboard_contact_false
from core.utils import texts
from core.utils.states import AddPhone, Contact
from core.database.queryDB import save_phone, get_client_info


async def enter_phone(message: Message, state: FSMContext):
    await message.answer('Введите сотовый')
    await state.set_state(AddPhone.phone)


async def add_phone(message: Message, state: FSMContext):
    log = logger.bind(chat_id=message.chat.id, first_name=message.chat.first_name)
    phone = texts.phone(message.text)
    employee = await oneC.get_employeeInfo(phone)
    if employee:
        shops = [[i['Магазин'], i['idМагазин']] for i in employee["Магазины"]]
        await save_phone(str(message.chat.id), phone)
        await state.set_state(Contact.menu)
        user_id = employee['id']
        await state.update_data(shops=shops, user_id=user_id, agent_name=employee['Наименование'])
        log.info('Сотрудник найден в базе 1С')
        client_info = await get_client_info(message.chat.id)
        admin_info = await oneC.get_employeeInfo(client_info.phone_number)
        text = await texts.employee_true(employee, phone, admin_info, client_info.admin)
        await message.answer(text, reply_markup=getKeyboard_contact_true(superadmin=client_info.admin, employee_info=employee, admin_info=admin_info))
    else:
        log.error('Сотрудник не найден в базе 1С')
        text = f"Данный контакт '<code>{phone}</code>' не зарегистрирован"
        await message.answer(text, reply_markup=getKeyboard_contact_false(phone))
