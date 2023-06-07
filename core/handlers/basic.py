import os.path

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile

import config
from core.database.queryDB import get_saved_phones
from core.keyboards.inline import getKeyboard_start, getKeyboard_contacts, getKeyboard_delete_contacts
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
        await message.answer(texts.error_head + "Вы еще не присылали ни одного контакта")


async def start_delete_contacts(message: Message, state: FSMContext):
    contacts = await get_saved_phones(chat_id=str(message.chat.id))
    await state.update_data(to_delete=[])
    if contacts:
        await message.answer("Выберите пользователя на удаление", reply_markup=await getKeyboard_delete_contacts(contacts))
    else:
        await message.answer(texts.error_head + "Вы еще не присылали ни одного контакта")
