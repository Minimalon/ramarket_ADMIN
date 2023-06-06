from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile
from loguru import logger

from core.database.ramarket_shop.db_shop import create_excel_by_shop_id
from core.keyboards.inline import getKeyboad_select_countries, getKeyboad_select_cities, getKeyboad_select_shop
from core.oneC.oneC import get_unique_countryes, get_cities_by_country_code, get_shops_by_city_code, get_shop_by_id
from core.utils import texts
from core.utils.callbackdata import Country, City, Shops
from core.utils.states import HistoryOrders


async def select_country(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Нажали кнопку "Историю продаж"')
    countries = await get_unique_countryes()
    await state.set_state(HistoryOrders.country)
    await call.message.edit_text("Выберите страну", reply_markup=getKeyboad_select_countries(countries))


async def select_city(call: CallbackQuery, callback_data: Country, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал страну "{callback_data.code}"')
    cities = await get_cities_by_country_code(callback_data.code)
    await state.set_state(HistoryOrders.city)
    await call.message.edit_text("Выберите город", reply_markup=getKeyboad_select_cities(cities))


async def select_shop(call: CallbackQuery, callback_data: City, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал город "{callback_data.code}"')
    shops = await get_shops_by_city_code(callback_data.code)
    await state.set_state(HistoryOrders.shops)
    await call.message.edit_text("Выберите город", reply_markup=getKeyboad_select_shop(shops))


async def send_history(call: CallbackQuery, callback_data: Shops, state: FSMContext, bot: Bot):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал магазин "{callback_data.code}"')
    shop_info = await get_shop_by_id(callback_data.code)
    path = await create_excel_by_shop_id(callback_data.code)
    if path:
        await bot.send_document(call.message.chat.id, document=FSInputFile(path))
        await state.clear()
    else:
        await call.message.answer(texts.error_head + "Данный магазин еще не делал продаж")
        await call.answer()
