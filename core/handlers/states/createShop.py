import re
from decimal import Decimal

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from core.keyboards.inline import getKeyboard_currencies, getKeyboard_kontragent, getKeyboad_select_countries, getKeyboad_select_cities, getKeyboard_createShop
from core.oneC.api import Api
from core.oneC.oneC import get_unique_countryes, get_cities_by_country_code, get_city_by_code, get_country_by_code
from core.utils import texts
from core.utils.callbackdata import CurrencyAll, Kontragent, Country, City
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


async def select_country(call: CallbackQuery, state: FSMContext, callback_data: Kontragent):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрали контрагента "{callback_data.id}"')
    await state.update_data(kontragent_id=callback_data.id)
    countries = await get_unique_countryes()
    await call.message.edit_text("Выберите страну", reply_markup=getKeyboad_select_countries(countries))


async def select_city(call: CallbackQuery, callback_data: Country, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал страну "{callback_data.code}"')
    await state.update_data(countryCode=callback_data.code)
    cities = await get_cities_by_country_code(callback_data.code)
    await call.message.edit_text("Выберите город", reply_markup=getKeyboad_select_cities(cities))


async def enter_shop_name(call: CallbackQuery, state: FSMContext, callback_data: City):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.set_state(CreateShop.name)
    await state.update_data(cityCode=callback_data.code)
    log.info(f'Выбрали магазин "{callback_data.code}"')
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
    name, inn, currency, kontragent_id, cityCode, countryCode = data['name'], data['inn'], data['currency'], data['kontragent_id'], data['cityCode'], data['countryCode']
    city, country = (await get_city_by_code(cityCode)), (await get_country_by_code(countryCode))
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
                          '<b>Страна</b>: <code>{country}</code>\n'
                          '<b>Город</b>: <code>{city}</code>\n'
                          '<b>ИНН</b>: <code>{inn}</code>\n'
                          '<b>Валюта</b>: <code>{currency}</code>\n'
                          '<b>Стоимость валюты</b>: <code>{price}</code>\n'
                          '<b>Контрагент</b>: <code>{kontragent_name}</code>').
                         format(name=name, inn=inn, currency=currency, price=price, kontragent_name=kontragent_name[0], city=city.name, country=country.name),
                         reply_markup=getKeyboard_createShop())
    await state.set_state(CreateShop.final)
    await state.update_data(currency_price=message.text)


async def createShop(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    data = await state.get_data()
    name, inn, currency, kontragent_id, cityCode, countryCode, currency_price = data['name'], data['inn'], data['currency'], data['kontragent_id'], data['cityCode'], \
        data['countryCode'], data['currency_price']
    log.info(name, inn, kontragent_id, currency, currency_price, cityCode, countryCode)
    response, response_text = await oneC.create_shop(name, inn, kontragent_id, currency, currency_price, cityCode, countryCode)
    if response.ok:
        log.success("Магазин успешно создан")
        await call.message.edit_text('Магазин успешно создан ✅')
    else:
        log.error(f'Код ответа сервера: {response.status}')
        await call.message.answer(await texts.error_server(response.status))
