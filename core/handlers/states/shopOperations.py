import re

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger

from core.database.queryDB import get_client_info
from core.database.ramarket_shop.db_shop import create_excel_by_shop, create_excel_by_agent_id, create_excel_by_shops
from core.keyboards.inline import getKeyboad_select_countries, getKeyboad_select_cities, getKeyboad_select_shop, getKeyboard_filters_history_orders, getKeyboad_orgs, \
    getKeyboard_shops_operations, getKeyboard_contracts
from core.oneC.oneC import *
from core.utils import texts
from core.utils.callbackdata import Country, City, Shops, Org, HistoryShopOrdersByDays, HistoryUserOrdersByDays, HistoryTotalShops, Contract
from core.utils.states import HistoryOrdersShop, HistoryOrdersUser, HistoryOrdersAll


async def select_org(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Нажали кнопку "Операции с магазинами"')
    client_info = await get_client_info(call.message.chat.id)
    if client_info.admin:
        await state.set_state(HistoryOrdersShop.org)
        await call.message.edit_text("Выберите юридическое лицо", reply_markup=getKeyboad_orgs(await get_orgs()))
    else:
        shops = await get_user_shops(client_info.phone_number)
        if not shops:
            await call.message.edit_text(texts.error_head + 'У вас не привязано ни одного магазина')
        await state.set_state(HistoryOrdersShop.shops)
        await call.message.edit_text("Выберите магазин", reply_markup=getKeyboad_select_shop(shops))


async def select_country(call: CallbackQuery, state: FSMContext, callback_data: Org):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал организацию "{callback_data.code}"')
    await state.update_data(org_id=callback_data.code)
    data = await state.get_data()
    countries = await get_unique_countryes(data['org_id'])
    if countries:
        await call.message.edit_text("Выберите страну", reply_markup=getKeyboad_select_countries(countries))
        await state.set_state(HistoryOrdersShop.country)
    else:
        await call.message.answer('У данного юридического лица нет зарегистрированных магазинов')


async def select_city(call: CallbackQuery, callback_data: Country, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал страну "{callback_data.code}"')
    data = await state.get_data()
    cities = await get_cities_by_country_code(callback_data.code, data['org_id'])
    await state.set_state(HistoryOrdersShop.city)
    await call.message.edit_text("Выберите город", reply_markup=getKeyboad_select_cities(cities))


async def select_shop(call: CallbackQuery, callback_data: City, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал город "{callback_data.code}"')
    data = await state.get_data()
    shops = await get_shops_by_city_code_and_org_id(callback_data.code, data['org_id'])
    await state.set_state(HistoryOrdersShop.shops)
    await call.message.edit_text("Выберите магазин", reply_markup=getKeyboad_select_shop(shops))


async def select_shop_operations(call: CallbackQuery, callback_data: Shops, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.update_data(shop_id=callback_data.code, org_id=callback_data.org_id)
    log.info(f'Выбрал магазин {callback_data.code}')
    await call.message.edit_text('Выберите нужную операцию', reply_markup=getKeyboard_shops_operations())


async def select_change_contract(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Изменить договор"')
    await call.answer('Данная функция еще в разработке')
    return
    data = await state.get_data()
    contracts = await get_contracts_by_org(data['org_id'])
    if contracts:
        await call.message.edit_text('Выберите нужную договор', reply_markup=getKeyboard_contracts(contracts))
    else:
        name = [_['Наименование'] for _ in await api.get_all_orgs() if _['ИНН'] == data['org_id']][0]
        await call.message.answer(texts.error_head + f'У данного юр.лица нет договоров {name}', reply_markup=getKeyboard_contracts(contracts))


async def change_contract(call: CallbackQuery, state: FSMContext, callback_data: Contract):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрали договор "{callback_data.id}"')
    data = await state.get_data()
    response, contracts = await api.update_shop_contract(data['org_id'])
    if contracts:
        await call.message.edit_text('Выберите нужную договор', reply_markup=getKeyboard_contracts(contracts))
    else:
        name = [_['Наименование'] for _ in await api.get_all_orgs() if _['ИНН'] == data['org_id']][0]
        await call.message.answer(texts.error_head + f'У данного юр.лица нет договоров {name}', reply_markup=getKeyboard_contracts(contracts))


async def select_history_orders(call: CallbackQuery):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await call.message.edit_text('Выберите нужный вид истории', reply_markup=await getKeyboard_filters_history_orders())


async def history_period(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('История продаж за промежуток времени')
    await call.message.edit_text("Введите полную дату <b><u>с</u></b> какого числа нужна история продаж\nДату нужно писать строго как в примере\nПример: <b><u>2023-06-01</u></b>")
    if call.data == 'history_period_shop':
        await state.set_state(HistoryOrdersShop.start_date)
    elif call.data == 'history_period_user':
        await state.set_state(HistoryOrdersUser.start_date)
    elif call.data == 'history_period_total_shops':
        await state.set_state(HistoryOrdersAll.start_date)


async def start_period(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info(f'start_date={message.text}')
    date = message.text.split('-')
    if len(date) == 3:
        year, month, day = date
        if len(year) != 4:
            log.error("len(year) != 4")
            await message.answer("{error}Неверно ввели <b><u>год</u></b>\nГод состоит из 4 цифр, а вы ввели {count}\nВведите полную дату снова"
                                 .format(error=texts.error_head, count=len(year)))
            return
        elif len(month) != 2:
            log.error("len(month) != 2")
            await message.answer("{error}Неверно ввели <b><u>месяц</u></b>\nМесяц состоит из 2 цифр, а вы ввели {count}\nВведите полную дату снова"
                                 .format(error=texts.error_head, count=len(month)))
            return
        elif len(day) != 2:
            log.error("len(day) != 2")
            await message.answer("{error}Неверно ввели <b><u>день</u></b>\nДень состоит из 2 цифр, а вы ввели {count}\nВведите полную дату снова"
                                 .format(error=texts.error_head, count=len(day)))
            return
        await message.answer("Введите полную дату <b><u>по</u></b> какое число нужна история продаж\nДату нужно писать строго как в примере\nПример: <b><u>2023-06-01</u></b>")
        if re.findall('HistoryOrdersShop', str(await state.get_state())):
            await state.set_state(HistoryOrdersShop.end_date)
        elif re.findall('HistoryOrdersUser', str(await state.get_state())):
            await state.set_state(HistoryOrdersUser.end_date)
        elif re.findall('HistoryOrdersAll', str(await state.get_state())):
            await state.set_state(HistoryOrdersAll.end_date)

        await state.update_data(start_period=message.text)
    else:
        await message.answer("{error}Неверно ввели дату\nПопробуйте снова\nПример: <b><u>2023-06-01</u></b>".format(error=texts.error_head))
        log.error("len(start_date) != 3")
        return


async def end_period(message: Message, state: FSMContext, bot: Bot):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info(f'end_date={message.text}')
    data = await state.get_data()
    date = message.text.split('-')
    if len(date) == 3:
        year, month, day = date
        if len(year) != 4:
            log.error("len(year) != 4")
            await message.answer("{error}Неверно ввели <b><u>год</u></b>\nГод состоит из 4 цифр, а вы ввели {count}\nВведите полную дату снова"
                                 .format(error=texts.error_head, count=len(year)))
            return
        elif len(month) != 2:
            log.error("len(month) != 2")
            await message.answer("{error}Неверно ввели <b><u>месяц</u></b>\nМесяц состоит из 2 цифр, а вы ввели {count}\nВведите полную дату снова"
                                 .format(error=texts.error_head, count=len(month)))
            return
        elif len(day) != 2:
            log.error("len(day) != 2")
            await message.answer("{error}Неверно ввели <b><u>день</u></b>\nДень состоит из 2 цифр, а вы ввели {count}\nВведите полную дату снова"
                                 .format(error=texts.error_head, count=len(day)))
            return

        start_date = data['start_period'].replace('-', '.')
        end_date = message.text.replace('-', '.')
        if re.findall('HistoryOrdersShop', str(await state.get_state())):
            shop_info = await get_shop_by_id(data["shop_id"])
            file_name = f"{'_'.join(shop_info.name.split())}__{start_date}|{end_date}"
            path = await create_excel_by_shop(data["shop_id"], file_name, start_date=data['start_period'], end_date=message.text)
            if path:
                await bot.send_document(message.chat.id, document=FSInputFile(path))
            else:
                await message.answer(texts.error_head + f"Данный магазин не делал продаж за данный период времени с {data['start_period']} по {message.text}")
        elif re.findall('HistoryOrdersUser', str(await state.get_state())):
            file_name = f"{'_'.join(data['agent_name'].split())}__{start_date}_{end_date}"
            path = await create_excel_by_agent_id(data['user_id'], file_name, start_date=data['start_period'], end_date=message.text)
            if path:
                await bot.send_document(message.chat.id, document=FSInputFile(path))
            else:
                await message.answer(texts.error_head + f"Данный пользователь не делал продаж за данный период времени с {data['start_period']} по {message.text}")
        elif re.findall('HistoryOrdersAll', str(await state.get_state())):
            response, all_shops = await api.get_all_shops()
            all_shops = [_['id'] for _ in all_shops]
            file_name = f"total_orders__{start_date}_{end_date}"
            path = await create_excel_by_shops(all_shops, file_name, start_date=data['start_period'], end_date=message.text)
            if path:
                await bot.send_document(message.chat.id, document=FSInputFile(path))
            else:
                await message.answer(texts.error_head + f"Магазины не делали продаж за данный период времени с {data['start_period']} по {message.text}")
    else:
        await message.answer("{error}Неверно ввели дату\nПопробуйте снова\nПример: <b><u>2023-06-12</u></b>".format(error=texts.error_head))
        log.error("len(end_date) != 3")
        return


async def send_history_all_days(call: CallbackQuery, state: FSMContext, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info("Отправил историю заказов за всё время")
    data = await state.get_data()
    shop_info = await get_shop_by_id(data["shop_id"])
    path = await create_excel_by_shop(data["shop_id"], f"{'_'.join(shop_info.name.split())}__all")
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
        await state.clear()
    else:
        await call.message.answer(texts.error_head + "Данный магазин еще не делал продаж")
        await call.answer()


async def send_history_total_shops_all_days(call: CallbackQuery, state: FSMContext, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info("Отправил историю заказов за всё время")
    response, all_shops = await api.get_all_shops()
    all_shops = [_['id'] for _ in all_shops]
    path = await create_excel_by_shops(all_shops, 'total_orders__all')
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
        await state.clear()
    else:
        await call.message.answer(texts.error_head + "Магазины еще не делали продаж")
        await call.answer()


async def history_shop_orders_by_days(call: CallbackQuery, state: FSMContext, bot: Bot, callback_data: HistoryShopOrdersByDays):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'История продаж магазина за {callback_data.days} дней')
    data = await state.get_data()
    start_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=callback_data.days), '%Y-%m-%d')
    end_date = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')
    shop_info = await get_shop_by_id(data["shop_id"])
    path = await create_excel_by_shop(data["shop_id"], f"{'_'.join(shop_info.name.split())}__{callback_data.days}days", start_date=start_date, end_date=end_date)
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
    else:
        await call.message.answer(texts.error_head + f"Данный магазин не делал продаж за данный период времени с {start_date} по {end_date}")
    await call.answer()


async def history_user_orders_by_days(call: CallbackQuery, state: FSMContext, bot: Bot, callback_data: HistoryUserOrdersByDays):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'История продаж пользователя за {callback_data.days} дней')
    start_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=callback_data.days), '%Y-%m-%d')
    end_date = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')
    data = await state.get_data()
    path = await create_excel_by_agent_id(data['user_id'], f"{'_'.join(data['agent_name'].split())}__{callback_data.days}days", start_date=start_date, end_date=end_date)
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
    else:
        await call.message.answer(texts.error_head + f"Данный пользователь не делал продаж за данный период времени с {start_date} по {end_date}")
    await call.answer()


async def history_total_shops(call: CallbackQuery, bot: Bot, callback_data: HistoryTotalShops):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'История продаж всех магазинов за {callback_data.days} дней')
    start_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=callback_data.days), '%Y-%m-%d')
    end_date = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')
    response, all_shops = await api.get_all_shops()
    all_shops = [_['id'] for _ in all_shops]
    path = await create_excel_by_shops(all_shops, f'total_orders__{callback_data.days}days', start_date=start_date, end_date=end_date)
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
    else:
        await call.message.answer(texts.error_head + f"Магазины не делали продаж за данный период времени с {start_date} по {end_date}")
    await call.answer()
