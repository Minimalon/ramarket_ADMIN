import datetime
import re

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from loguru import logger

from core.database.ramarket_shop.db_shop import create_excel_by_shop, create_excel_by_agent_id
from core.keyboards.inline import getKeyboad_select_countries, getKeyboad_select_cities, getKeyboad_select_shop, getKeyboard_filters_history_orders, getKeyboad_orgs
from core.oneC.oneC import get_unique_countryes, get_cities_by_country_code, get_shops_by_city_code_and_org_id, get_shop_by_id, get_orgs
from core.utils import texts
from core.utils.callbackdata import Country, City, Shops, Org, HistoryShopOrdersByDays, HistoryUserOrdersByDays
from core.utils.states import HistoryOrdersShop, HistoryOrdersUser


async def select_org(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Нажали кнопку "Историю продаж"')
    await state.set_state(HistoryOrdersShop.org)
    await call.message.edit_text("Выберите юридическое лицо", reply_markup=getKeyboad_orgs(await get_orgs()))


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
    await call.message.edit_text("Выберите город", reply_markup=getKeyboad_select_shop(shops))


async def select_filter_order(call: CallbackQuery, callback_data: Shops, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    await state.update_data(code=callback_data.code)
    log.info(f'Выбрал магазин {callback_data.code}')
    await call.message.edit_text('Выберите нужный вид истории', reply_markup=await getKeyboard_filters_history_orders())


async def history_period(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('История продаж за промежуток времени')
    await call.message.edit_text("Введите полную дату <b><u>с</u></b> какого числа нужна история продаж\nДату нужно писать строго как в примере\nПример: <b><u>2023-06-01</u></b>")
    if call.data == 'history_period_shop':
        await state.set_state(HistoryOrdersShop.start_date)
    else:
        await state.set_state(HistoryOrdersUser.start_date)


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
        else:
            await state.set_state(HistoryOrdersUser.end_date)

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

        if re.findall('HistoryOrdersShop', str(await state.get_state())):
            shop_info = await get_shop_by_id(data["code"])
            path = await create_excel_by_shop(data["code"], shop_info.name, start_date=data['start_period'], end_date=message.text)
            if path:
                await bot.send_document(message.chat.id, document=FSInputFile(path))
            else:
                await message.answer(texts.error_head + f"Данный магазин не делал продаж за данный период времени с {data['start_period']} по {message.text}")
        else:
            path = await create_excel_by_agent_id(data['user_id'], data['agent_name'], start_date=data['start_period'], end_date=message.text)
            if path:
                await bot.send_document(message.chat.id, document=FSInputFile(path))
            else:
                await message.answer(texts.error_head + f"Данный пользователь не делал продаж за данный период времени с {data['start_period']} по {message.text}")

    else:
        await message.answer("{error}Неверно ввели дату\nПопробуйте снова\nПример: <b><u>2023-06-12</u></b>".format(error=texts.error_head))
        log.error("len(end_date) != 3")
        return


async def send_history_all_days(call: CallbackQuery, state: FSMContext, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info("Отправил историю заказов за всё время")
    data = await state.get_data()
    shop_info = await get_shop_by_id(data["code"])
    path = await create_excel_by_shop(data["code"], shop_info.name)
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
        await state.clear()
    else:
        await call.message.answer(texts.error_head + "Данный магазин еще не делал продаж")
        await call.answer()


async def history_shop_orders_by_days(call: CallbackQuery, state: FSMContext, bot: Bot, callback_data: HistoryShopOrdersByDays):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'История продаж магазина за {callback_data.days} дней')
    data = await state.get_data()
    start_date = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=callback_data.days), '%Y-%m-%d')
    end_date = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1), '%Y-%m-%d')
    shop_info = await get_shop_by_id(data["code"])
    path = await create_excel_by_shop(data["code"], shop_info.name, start_date=start_date, end_date=end_date)
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
    path = await create_excel_by_agent_id(data['user_id'], data['agent_name'], start_date=start_date, end_date=end_date)
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
    else:
        await call.message.answer(texts.error_head + f"Данный пользователь не делал продаж за данный период времени с {start_date} по {end_date}")
    await call.answer()
