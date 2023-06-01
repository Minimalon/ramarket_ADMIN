import re
from decimal import Decimal
from loguru import logger
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from core.keyboards.inline import getKeyboard_currencies, getKeyboard_kontragent
from core.oneC.api import Api
from core.utils import texts
from core.utils.callbackdata import CurrencyAll, Kontragent
from core.utils.states import CreateShop

oneC = Api()


async def select_currency(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.set_state(CreateShop.currencies)
    log.info('Нажали кнопку "Создать магазин"')
    await call.message.edit_text('Выберите валюту', reply_markup=getKeyboard_currencies())


async def select_kontagent(call: CallbackQuery, state: FSMContext, callback_data: CurrencyAll):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.set_state(CreateShop.kontragent)
    await state.update_data(currency=callback_data.currency)
    log.info(f'Выбрали валюту "{callback_data.currency}"')
    await call.message.edit_text('Выберите контрагента', reply_markup=await getKeyboard_kontragent())


async def enter_shop_name(call: CallbackQuery, state: FSMContext, callback_data: Kontragent):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.set_state(CreateShop.name)
    await state.update_data(kontragent_id=callback_data.id)
    log.info(f'Выбрали контрагента "{callback_data.id}"')
    await call.message.edit_text('Напишите название магазина')


async def enter_org_inn(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    await state.set_state(CreateShop.org)
    await state.update_data(name=message.text)
    log.info(f'Написали название магазина "{message.text}"')
    await message.answer('Напишите ИНН вашей организации')


async def enter_shop_currency_price(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    if not message.text.isdigit():
        await message.answer(texts.error_head + "ИНН состоит только из цифр\nНапишите еще раз")
        log.error(f'Написали ИНН "{message.text}"')
        return
    await state.set_state(CreateShop.currency_price)
    log.info(f'Написали ИНН "{message.text}"')
    await state.update_data(inn=message.text)
    await message.answer('Напишите стоимость курса магазина\nЕго можно будет в дальнейшем изменить')


async def final(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    data = await state.get_data()
    name, inn, currency, kontragent_id = data['name'], data['inn'], data['currency'], data['kontragent_id']
    price = message.text
    if re.findall(',', price):
        price = price.replace(',', '.')
    if not price.isdecimal() and not price.isdigit():
        await message.answer(texts.error_head + "Стоимость состоит только из цифр\nНапишите еще раз")
        return
    log.info(f'Ввели стоимость курс "{price}"')
    price = Decimal(price).quantize(Decimal('1.0000'))
    kontragent_name = [agent['Наименование'] for agent in await oneC.get_all_kontragents() if agent['Id'] == kontragent_id]
    await message.answer(('ℹ️Информацияℹ️\n'
                          '➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n'
                          '<b>Название</b>: <code>{name}</code>\n'
                          '<b>ИНН</b>: <code>{inn}</code>\n'
                          '<b>Валюта</b>: <code>{currency}</code>\n'
                          '<b>Стоимость валюты</b>: <code>{price}</code>\n'
                          '<b>Контрагент</b>: <code>{kontragent_name}</code>').format(name=name, inn=inn, currency=currency, price=price, kontragent_name=kontragent_name[0]))
    await state.set_state(CreateShop.final)
    await state.update_data(currency_price=message.text)


async def createShop(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    data = await state.get_data()
    name, inn,  kontragent_id, currency, currency_price = data['name'], data['inn'], data['kontragent_id'], data['currency'], data['currency_price']
    response, response_text = await oneC.create_shop(name, inn,  kontragent_id, currency, currency_price)
    if response.ok:
        log.success("Магазин успешно создан")
        await call.message.edit_text('Магазин успешно создан ✅')
    else:
        log.error(f'Код ответа сервера: {response.status}')
        await call.message.answer(await texts.error_server(response.status))

