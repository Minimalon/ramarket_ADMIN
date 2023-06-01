import re
from decimal import Decimal

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from core.keyboards.inline import getKeyboard_start
from core.oneC.api import Api
from core.utils import texts
from core.utils.callbackdata import CurrencyAll
from core.utils.states import UpdateCurrencyPriceAll


async def get_price(call: CallbackQuery, state: FSMContext, callback_data: CurrencyAll):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали кнопку "Изменить стоимость курса"')
    await state.update_data(currency=callback_data.currency)
    await call.message.answer('Введите новую стоимость валюты')
    await state.set_state(UpdateCurrencyPriceAll.price)


async def update_price(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    price = message.text
    log.info(f'Ввели цену "{price}"')
    if re.findall(',', message.text):
        if len(message.text.split(',')) > 2:
            await message.answer(f"{texts.error_head}Ввод цены разрешен через точку\nПример как надо: <b>10.12</b>")
            return
        price = price.replace(',', '.')

    check_price = price.replace('.', '')
    if not check_price.isdecimal():
        await message.answer(
            f"{texts.error_head}Цена содержит не нужные символы\nПопробуйте снова\nПример как надо: <u><b>10.12</b></u>")
        return
    price = str(Decimal(price).quantize(Decimal('1.0000')))
    response, text = await Api().update_currency_all(data.get('currency'), price)
    if response.ok:
        await message.answer(f'✅Стоимость валюты "<b><u>{data.get("currency")}</u></b>" успешно изменена')
        await bot.send_message(message.chat.id, texts.menu, reply_markup=getKeyboard_start())
        await state.clear()
    else:
        await message.answer(
            f'{texts.error_head}Стоимость валюты не изменена.\nКод ответа сервера "{response.status}"\n'
            f'Попробуйте ввести стоимость курса еще раз.')
        log.error(f'Стоимость валюты не изменена {response.status, text}')
