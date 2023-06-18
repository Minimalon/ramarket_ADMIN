import os.path
from collections import namedtuple
from operator import attrgetter

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile

import config
from core.database.queryDB import get_saved_phones
from core.database.ramarket_shop.db_shop import get_orders_by_1c_id
from core.keyboards.inline import getKeyboard_start, getKeyboard_contacts, getKeyboard_delete_contacts, getKeyboard_all_contacts, getKeyboard_start_delete_users
from core.oneC.api import Api
from core.utils import texts

oneC = Api()


async def get_start(message: Message):
    await message.answer(texts.menu, reply_markup=getKeyboard_start())


async def video_tutorial(message: Message, bot: Bot):
    path = os.path.join(config.dir_path, 'files', 'tutorial.MP4')
    await bot.send_video(message.chat.id, video=FSInputFile(path))


async def contacts(message: Message):
    contacts = await get_saved_phones(chat_id=str(message.chat.id))
    if contacts:
        await message.answer("Выберите нужного пользователя", reply_markup=await getKeyboard_contacts(contacts))
    else:
        await message.answer(texts.error_head + "Список сохраненных контактов пуст")


async def all_users(message: Message):
    response, all_users = await oneC.get_all_users()
    if response.ok:
        contact = namedtuple('contact', 'name id phone count_total_orders')
        contacts = []
        for user in all_users:
            if user['Телефон'] in ['79934055804']:  # Не показывает контакты в /all_users
                continue
            count_total_orders = len(await get_orders_by_1c_id(user['id']))
            contacts.append(contact(f"{user['Наименование']}", user['id'], user['Телефон'], count_total_orders))
        contacts = sorted(contacts, key=attrgetter('count_total_orders'), reverse=True)
        await message.answer("Выберите нужного пользователя", reply_markup=await getKeyboard_all_contacts(contacts))
    else:
        await message.answer(await texts.error_server(response))


async def start_delete_users(message: Message):
    response, contacts = await oneC.get_all_users()
    if response.ok:
        await message.answer("Выберите нужного пользователя для удаления", reply_markup=await getKeyboard_start_delete_users(contacts))
    else:
        await message.answer(await texts.error_server(response))


async def start_delete_contacts(message: Message, state: FSMContext):
    contacts = await get_saved_phones(chat_id=str(message.chat.id))
    await state.update_data(to_delete=[])
    if contacts:
        await message.answer("Выберите пользователя на удаление", reply_markup=await getKeyboard_delete_contacts(contacts))
    else:
        await message.answer(texts.error_head + "Список сохраненных контактов пуст")
