import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from core.database.queryDB import save_phone
from core.keyboards.inline import getKeyboard_select_admin, getKeyboard_contact_true, getKeyboard_contact_false
from core.oneC.api import Api
from core.utils import texts
from core.utils.callbackdata import CreateEmployee, EmployeeAdmin
from core.utils.states import StatesCreateEmployee, Contact
from core.oneC import oneC
api = Api()


async def select_admin(call: CallbackQuery, state: FSMContext, callback_data: CreateEmployee):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Создают сотрудника "{callback_data.phone}"')
    await state.update_data(phone=callback_data.phone)
    await state.set_state(StatesCreateEmployee.admin)
    await call.message.edit_text('Данный сотрудник администратор?', reply_markup=getKeyboard_select_admin())


async def name(call: CallbackQuery, state: FSMContext, callback_data: EmployeeAdmin):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Администратор "{callback_data.admin}"')
    await state.update_data(admin=callback_data.admin)
    await state.set_state(StatesCreateEmployee.name)
    await call.message.edit_text("Введите полное ФИО сотдруника")


async def final_create_empliyee(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    data = await state.get_data()
    admin, phone = data['admin'], data['phone']
    name = message.text
    log.info(f'Ввели ФИО "{name}"')
    if len(name.split()) == 3:
        await api.create_employ(name, admin, phone)
        await asyncio.sleep(2)
        await save_phone(str(message.chat.id), phone)
        employee = await oneC.get_employeeInfo(phone)
        if employee:
            await state.set_state(Contact.menu)
            shops = [[i['Магазин'], i['idМагазин']] for i in employee["Магазины"]]
            user_id = employee['id']
            await state.update_data(shops=shops, user_id=user_id)
            text = await texts.employee_true(employee, phone)
            await message.answer(text, reply_markup=getKeyboard_contact_true())
        else:
            log.error('Сотрудник не найден в базе 1С после его создания')
            text = f"Данный контакт '<code>{phone}</code>' не зарегистрирован"
            await message.answer(text, reply_markup=getKeyboard_contact_false(phone))
            await message.answer(text)
    else:
        await message.answer('{text}'.format(text=texts.error_full_name(name)))
