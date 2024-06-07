import os.path
from collections import namedtuple
from datetime import datetime
from operator import attrgetter

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, CallbackQuery
from loguru import logger

import config
from core.database.queryDB import get_saved_phones, get_admins
from core.database.ramarket_shop.db_shop import get_orders_by_1c_id, get_orders_by_order_id, delete_orders_by_order_id, \
    prepare_delete_history_order
from core.keyboards import inline
from core.keyboards.inline import getKeyboard_start, getKeyboard_contacts, getKeyboard_delete_contacts, \
    getKeyboard_all_contacts, getKeyboard_start_delete_users, \
    getKeyboard_filters_total_shop_history_orders
from core.oneC.api import Api
from core.utils import texts
from core.utils.states import DeleteOrderState

oneC = Api()


async def get_start(message: Message):
    await message.answer(texts.menu, reply_markup=getKeyboard_start())


async def video_tutorial(message: Message, bot: Bot):
    path = os.path.join(config.dir_path, 'files', 'tutorial.MP4')
    await bot.send_video(message.chat.id, video=FSInputFile(path))


async def test(message: Message):
    raise ValueError('123')


async def contacts(message: Message):
    contacts = await get_saved_phones(chat_id=str(message.chat.id))
    if contacts:
        await message.answer("Выберите нужного пользователя", reply_markup=await getKeyboard_contacts(contacts))
    else:
        await message.answer(texts.error_head + "Список сохраненных контактов пуст")


async def all_users(message: Message):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    admin = await get_admins(message.chat.id)
    if not admin:
        await message.answer(texts.error_head + "Вы не суперадмин")
        log.error("Не суперадмин")
        return
    response, all_users = await oneC.get_all_users()
    if response.ok:
        contact = namedtuple('contact', 'name id phone count_total_orders')
        contacts = []
        for user in all_users:
            if user['Телефон'] in ['79934055804', ]:
                continue
            count_total_orders = len(await get_orders_by_1c_id(user['id'], None))
            contacts.append(contact(f"{user['Наименование']}", user['id'], user['Телефон'], count_total_orders))
        contacts = sorted(contacts, key=attrgetter('count_total_orders'), reverse=True)
        await message.answer("Выберите нужного пользователя", reply_markup=await getKeyboard_all_contacts(contacts))
    else:
        await message.answer(await texts.error_server(response))


async def start_delete_users(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    admin = await get_admins(message.chat.id)
    await state.update_data(to_delete_1c=[])
    if not admin:
        await message.answer(texts.error_head + "Вы не суперадмин")
        log.error("Не суперадмин")
        return
    response, contacts = await oneC.get_all_users()
    contacts = [_ for _ in contacts
                if _['Телефон'] not in ['79934055804', ] and _['id'] != '7402672']
    if response.ok:
        await message.answer("Выберите нужного пользователя для удаления",
                             reply_markup=await getKeyboard_start_delete_users(contacts))
    else:
        await message.answer(await texts.error_server(response))


async def start_delete_order(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    admin = await get_admins(message.chat.id)
    if not admin:
        await message.answer(texts.error_head + "Вы не суперадмин")
        log.error("Не суперадмин")
        return
    await state.set_state(DeleteOrderState.orderID)
    log.info('Нажали кнопку "Удалить чек"')
    await message.answer("Напишите номер заказа")


async def accept_orderID_delete_order(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info(f'Написали номер заказа "{message.text}"')
    orders = await get_orders_by_order_id(message.text)
    if len(orders) == 0:
        await message.answer(texts.error_head + 'Заказ не найден')
        log.error('Заказ не найден')
        return
    elif len(orders) > 1:
        await message.answer("Найдено больше одного заказа\n"
                             "Выберите заказ, который хотите удалить",
                             reply_markup=inline.kb_select_delete_order(orders))
        log.info("Найдено больше одного заказа")
    else:
        await delete_orders_by_order_id(message.text)
        r, text = await oneC.delete_order(orders[0].order_id, orders[0].date.strftime('%Y%m%d%H%M'))
        if r.ok:
            await message.answer(
                f'<b><u>Заказ удалён❌</u></b>\n'
                f'<b>Номер заказа</b>: <code>{message.text}</code>'
            )
            log.success(f"Заказ удалён '{message.text}'")
        else:
            await message.answer(text)
            log.error(text)


async def accept_date_delete_order(call: CallbackQuery, state: FSMContext, callback_data: DeleteOrderState):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрали чек для удаления "{callback_data.date}" "{callback_data.orderID}"')
    date_order = datetime.strptime(callback_data.date, '%Y%m%d%H%M')
    await oneC.delete_order(callback_data.orderID, date_order.strftime('%d.%m.%Y %H:%M:%S'))
    await prepare_delete_history_order(callback_data.orderID, date_order)
    await call.message.answer(
        f'<b><u>Заказ удалён❌</u></b>\n<b>Номер заказа</b>: <code>{callback_data.orderID}</code>')
    log.success(f'Удалили заказ {callback_data.orderID}')


async def start_delete_contacts(message: Message, state: FSMContext):
    contacts = await get_saved_phones(chat_id=str(message.chat.id))
    await state.update_data(to_delete=[])
    if contacts:
        await message.answer("Выберите пользователя на удаление",
                             reply_markup=await getKeyboard_delete_contacts(contacts))
    else:
        await message.answer(texts.error_head + "Список сохраненных контактов пуст")


async def filter_total_orders(message: Message):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    admin = await get_admins(message.chat.id)
    if not admin:
        await message.answer(texts.error_head + "Вы не суперадмин")
        log.error("Не суперадмин")
        return
    await message.answer("Выберите пользователя на удаление",
                         reply_markup=await getKeyboard_filters_total_shop_history_orders())


async def create_kontragent(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info(f'Написали название контрагента "{message.text}"')
    response, response_text = await oneC.create_kontragent(message.text)
    if response.ok:
        log.success('Контрагент создан')
        await message.answer(f"Контрагент <b><u>{message.text}</u></b> успешно создан")
    else:
        log.error(response_text)
        await message.answer(texts.error_head + 'Контрагент не создан')
        await message.answer(texts.error_head + response_text)
    await state.clear()
