import re
from decimal import Decimal

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from core.keyboards.inline import getKeyboard_shop_remove, getKeyboard_shop_add, getKeyboard_shop_change_currency_price, \
    getKeyboard_start, getKeyboad_select_countries, getKeyboad_select_cities, getKeyboad_orgs
from core.oneC.oneC import *
from core.utils import texts
from core.utils.callbackdata import RemoveShop, AddShop, CurrencyOneShop, City, Country, Org
from core.utils.states import OneShopCurrency


async def select_org(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Нажали кнопку "Прикрепить магазин"')
    await call.message.edit_text("Выберите юридическое лицо", reply_markup=getKeyboad_orgs(await get_orgs()))


async def select_country(call: CallbackQuery, state: FSMContext, callback_data: Org):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал организацию "{callback_data.code}"')
    await state.update_data(org_id=callback_data.code)
    countries = await get_unique_countryes(callback_data.code)
    if countries:
        await call.message.edit_text("Выберите страну", reply_markup=getKeyboad_select_countries(countries))
    else:
        await call.message.answer('У данного юридического лица нет зарегистрированных магазинов')


async def select_city(call: CallbackQuery, state: FSMContext, callback_data: Country):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал страну "{callback_data.code}"')
    data = await state.get_data()
    cities = await get_cities_by_country_code(callback_data.code, data['org_id'])
    await call.message.edit_text("Выберите город", reply_markup=getKeyboad_select_cities(cities))


async def start_add_shop(call: CallbackQuery, state: FSMContext, callback_data: City):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Прикрепить магазин"')
    data = await state.get_data()
    response, all_shops = await Api().get_all_shops()
    if response.ok:
        shops = await get_shops_by_city_code_and_org_id(callback_data.code, data['org_id'])
        await call.message.edit_text('Выберите магазин', reply_markup=getKeyboard_shop_add(shops, data.get('user_id'), data.get('addShops')))
        await state.update_data(cityCode=callback_data.code)
    else:
        log.error(f'Код ответа сервера: {response.status}')
        await call.message.answer(await texts.error_server(response.status))


async def select_add_shop(call: CallbackQuery, state: FSMContext, callback_data: AddShop):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    shop_id, user_id = callback_data.shop_id, callback_data.user_id
    data = await state.get_data()
    addShops = data.get('addShops')
    if not addShops:
        await state.update_data(addShops=[shop_id])
        addShops = [shop_id]
    else:
        if shop_id not in addShops:
            addShops.append(shop_id)
            await state.update_data(addShops=addShops)
        else:
            addShops.remove(callback_data.shop_id)
            await state.update_data(addShops=addShops)

    all_shops = await get_shops_by_city_code_and_org_id(data['cityCode'], data['org_id'])
    shops = [shop
             for shop in all_shops
             if shop.code not in [s[1] for s in data.get('shops')]]
    shop_name = [shop.name for shop in all_shops if shop.code == shop_id][0]
    log.info(f'Выбрали магазин "{shop_name}"')
    await call.message.edit_reply_markup(reply_markup=getKeyboard_shop_add(shops=shops, user_id=user_id, addShop=addShops))


async def add_shops(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    data = await state.get_data()
    addShops = data.get('addShops')
    response, all_shops = await Api().get_all_shops()
    if response.ok:
        shops = [shop['Наименование']
                 for shop in all_shops
                 if shop['id'] in addShops]
        await Api().user_add_shop(data.get('user_id'), addShops)
        await asyncio.sleep(5)
        if len(addShops) == 1:
            await call.message.edit_text(f'Магазин успешно прикреплён <b>{shops[0]}</b> ✅')
        else:
            await call.message.edit_text(f'Магазины успешно прикреплёны <b><u>{",".join(shops)}</u></b> ✅')
        await state.update_data(addShops=None)
    else:
        log.error(f'Код ответа сервера: {response.status}')
        await call.message.answer(await texts.error_server(response.status))


async def start_remove_shop(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Удалить магазин"')
    data = await state.get_data()
    response, all_shops = await Api().get_all_shops()
    if response.ok:
        await call.message.edit_text('Выберите магазин', reply_markup=getKeyboard_shop_remove(data.get('shops'), data.get('user_id'), data.get('removeShops')))
    else:
        log.error(f'Код ответа сервера: {response.status}')
        await call.message.answer(await texts.error_server(response.status))


async def select_remove_shop(call: CallbackQuery, state: FSMContext, callback_data: RemoveShop):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    shop_id, user_id = callback_data.shop_id, callback_data.user_id
    data = await state.get_data()
    removeShops = data.get('removeShops')
    if not removeShops:
        await state.update_data(removeShops=[shop_id])
        removeShops = [shop_id]
    else:
        if shop_id not in removeShops:
            removeShops.append(shop_id)
            await state.update_data(removeShops=removeShops)
        else:
            removeShops.remove(callback_data.shop_id)
            await state.update_data(removeShops=removeShops)

    response_all_shops, all_shops = await Api().get_all_shops()
    shop_name = [shop['Наименование'] for shop in all_shops if shop['id'] == shop_id][0]
    log.info(f'Выбрали магазин "{shop_name}"')
    if response_all_shops.ok:
        print(removeShops)
        await call.message.edit_reply_markup(reply_markup=getKeyboard_shop_remove(shops=data.get('shops'), user_id=user_id, removeShop=removeShops))
    else:
        await call.message.answer(await texts.error_server(response_all_shops.status))
        log.error(f'Магазин "{shop_name}" не прикреплён. Код ответа сервера: {response_all_shops.status}')


async def remove_shops(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    data = await state.get_data()
    removeShops = data.get('removeShops')
    response, all_shops = await Api().get_all_shops()
    if response.ok:
        shops = [shop['Наименование']
                 for shop in all_shops
                 if shop['id'] in removeShops]
        await Api().user_remove_shop(data.get('user_id'), removeShops)
        await asyncio.sleep(5)
        if len(removeShops) == 1:
            await call.message.edit_text(f'Магазин успешно удалён <b>{shops[0]}</b> ✅')
        else:
            await call.message.edit_text(f'Магазины успешно удалены <b><u>{",".join(shops)}</u></b> ✅')
        await state.update_data(removeShops=None)
    else:
        log.error(f'Код ответа сервера: {response.status}')
        await call.message.answer(await texts.error_server(response.status))


async def select_currency_price_shop(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Изменить курс магазина"')
    data = await state.get_data()
    await call.message.edit_text('Выберите магазин', reply_markup=getKeyboard_shop_change_currency_price(data))


async def enter_new_price(call: CallbackQuery, state: FSMContext, callback_data: CurrencyOneShop):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    shop_id = callback_data.shop_id
    log.info(f'Выбрали магазин "{shop_id}"')
    await call.message.edit_text('Введите новую стоимость валюты')
    response, shops = await Api().get_all_shops()
    shop_name = [s['Наименование'] for s in shops if s['id'] == shop_id][0]
    if response.ok:
        await state.update_data(shop_id=shop_id, shop_name=shop_name)
        await state.set_state(OneShopCurrency.price)
    else:
        await call.message.answer(await texts.error_server(response.status))
        log.error(f'Сервер не доступен. Код ответа сервера: {response.status}')


async def chage_currency_price_one_shop(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    shop_id, shop_name = data.get('shop_id'), data.get('shop_name')
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
    response, text = await Api().change_currency_one_shop(shop_id, price)
    if response.ok:
        await message.answer(f'✅Стоимость валюты "<b><u>{shop_name}</u></b>" успешно изменена')
        await bot.send_message(message.chat.id, texts.menu, reply_markup=getKeyboard_start())
        await state.clear()
    else:
        await message.answer(
            f'{texts.error_head}Стоимость валюты не изменена.\nКод ответа сервера "{response.status}"\n'
            f'Попробуйте ввести стоимость курса еще раз.')
        log.error(f'Стоимость валюты не изменена. Status:{response.status}, Text:{text}')
