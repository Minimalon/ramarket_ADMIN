from loguru import logger

from aiogram.fsm.context import FSMContext
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from core.oneC import oneC
from core.keyboards.inline import getKeyboard_contact_true, getKeyboard_contact_false
from core.utils import texts
from core.utils.states import AddPhone
from core.database.queryDB import save_phone


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
        user_id = employee['id']
        await state.update_data(shops=shops, user_id=user_id)
        log.info('Сотрудник найден в базе 1С')
        text = await texts.employee_true(employee, phone)
        await message.answer(text, reply_markup=getKeyboard_contact_true())
    else:
        log.error('Сотрудник не найден в базе 1С')
        text = f"Данный контакт '<code>{phone}</code>' не зарегистрирован"
        await message.answer(text, reply_markup=getKeyboard_contact_false(phone))
    await state.clear()
