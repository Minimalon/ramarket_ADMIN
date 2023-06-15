#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

import asyncio
import os

import aiogram.exceptions
from aiogram import Dispatcher, F, Bot
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger

import config
from core.database.model import init_models
from core.handlers import contact
from core.handlers.basic import get_start, video_tutorial, contacts, start_delete_contacts, all_users, start_delete_users
from core.handlers.callback import select_to_delete_contacts, select_currency, history_one_user_all_days, delete_contacts, functions_shop, select_to_delete_users, delete_users, \
    select_filter_user_history_orders
from core.handlers.states import shops, createShop, addContact, createEmployee, historyOrders
from core.handlers.states.updateCurrencyPriceAll import get_price, update_price
from core.middlewares.checkReg import CheckRegistrationCallbackMiddleware, CheckRegistrationMessageMiddleware
from core.utils.callbackdata import SavedContact, DeleteContact, CreateEmployee, EmployeeAdmin, Country, City, Shops, Currencyes, Kontragent, RemoveShop, AddShop, CurrencyOneShop, \
    Org, DeleteUsers, HistoryShopOrdersByDays, HistoryUserOrdersByDays
from core.utils.commands import get_commands, get_commands_admins
from core.utils.states import AddPhone, StatesCreateEmployee, HistoryOrdersShop, CreateShop, UpdateCurrencyPriceAll, Contact, OneShopCurrency, HistoryOrdersUser


@logger.catch()
async def start():
    if not os.path.exists(os.path.join(config.dir_path, 'logs')):
        os.makedirs(os.path.join(config.dir_path, 'logs'))
    logger.add(os.path.join(config.dir_path, 'logs', 'debug.log'),
               format="{time} | {level} | {name}:{function}:{line} | {message} | {extra}", )

    bot = Bot(token=config.token, parse_mode='HTML')
    await get_commands(bot)
    await get_commands_admins(bot, config.admins)
    await init_models()

    storage = RedisStorage.from_url(config.redisStorage)
    dp = Dispatcher(storage=storage)

    # MiddleWares
    dp.message.middleware(CheckRegistrationMessageMiddleware())
    dp.callback_query.middleware(CheckRegistrationCallbackMiddleware())

    # Команды
    dp.message.register(get_start, Command(commands=['start']))
    dp.message.register(video_tutorial, Command(commands=['help']))
    dp.message.register(contacts, Command(commands=['contacts']))
    dp.message.register(addContact.enter_phone, Command(commands=['add_contact']))
    dp.message.register(start_delete_contacts, Command(commands=['delete_contacts']))
    dp.message.register(all_users, Command(commands=['all_users']))
    dp.message.register(start_delete_users, Command(commands=['delete_users']))

    # Сохранённые пользователи
    dp.callback_query.register(contact.get_saved_contact, SavedContact.filter())
    dp.message.register(addContact.add_phone, AddPhone.phone)
    # Удалить сохранённых пользователей
    dp.callback_query.register(select_to_delete_contacts, DeleteContact.filter())
    dp.callback_query.register(delete_contacts, F.data == 'deleteContacts')
    # Удалить пользователей из 1С
    dp.callback_query.register(select_to_delete_users, DeleteUsers.filter())
    dp.callback_query.register(delete_users, F.data == 'deleteUsers')

    # Регистрация контакта
    dp.message.register(contact.get_contact, F.contact)
    # Создание нового сотрудника
    dp.callback_query.register(createEmployee.select_admin, CreateEmployee.filter())
    dp.callback_query.register(createEmployee.name, EmployeeAdmin.filter())
    dp.message.register(createEmployee.final_create_empliyee, StatesCreateEmployee.name)

    # Главное меню
    dp.callback_query.register(select_currency, F.data == 'changeCurrencyPrice')
    dp.callback_query.register(createShop.select_currency, F.data == 'startCreateShop')
    dp.callback_query.register(historyOrders.select_org, F.data == 'historyOrders')

    # История продаж по магазину
    dp.callback_query.register(historyOrders.select_country, Org.filter(), HistoryOrdersShop.org)
    dp.callback_query.register(historyOrders.select_city, Country.filter(), HistoryOrdersShop.country)
    dp.callback_query.register(historyOrders.select_shop, City.filter(), HistoryOrdersShop.city)
    dp.callback_query.register(historyOrders.select_filter_order, Shops.filter(), HistoryOrdersShop.shops)
    dp.callback_query.register(historyOrders.send_history_all_days, F.data == 'history_all_days')
    dp.callback_query.register(historyOrders.history_period, F.data == 'history_period_shop')
    dp.message.register(historyOrders.start_period, HistoryOrdersShop.start_date)
    dp.message.register(historyOrders.end_period, HistoryOrdersShop.end_date)
    # История продаж по магазину за промежуток времени
    dp.callback_query.register(historyOrders.history_shop_orders_by_days, HistoryShopOrdersByDays.filter())

    # История продаж по пользователю
    dp.callback_query.register(select_filter_user_history_orders, F.data == 'historyOrdersOneUser')
    dp.callback_query.register(history_one_user_all_days, F.data == 'orders_user_all_days')
    dp.callback_query.register(historyOrders.history_shop_orders_by_days, HistoryUserOrdersByDays.filter())
    dp.callback_query.register(historyOrders.history_period, F.data == 'history_period_user')
    dp.message.register(historyOrders.start_period, HistoryOrdersUser.start_date)
    dp.message.register(historyOrders.end_period, HistoryOrdersUser.end_date)
    # Создание магазина
    dp.callback_query.register(createShop.select_kontragent, Currencyes.filter(), CreateShop.currencies)
    dp.callback_query.register(createShop.select_org, Kontragent.filter(), CreateShop.kontragent)
    dp.callback_query.register(createShop.select_country, Org.filter(), CreateShop.kontragent)
    dp.callback_query.register(createShop.select_city, Country.filter(), CreateShop.kontragent)
    dp.callback_query.register(createShop.enter_shop_name, City.filter(), CreateShop.kontragent)
    dp.message.register(createShop.final, CreateShop.name)
    dp.callback_query.register(createShop.createShop, F.data == 'createShop')

    # Изменить стоимость курса у всех магазинов
    dp.callback_query.register(get_price, Currencyes.filter())
    dp.message.register(update_price, UpdateCurrencyPriceAll.price)
    # region Действия с полученным контактом
    # Меню
    dp.callback_query.register(functions_shop, F.data == 'storeFunctions')
    # Удалить магазин с контакта
    dp.callback_query.register(shops.start_remove_shop, F.data == 'remove_shop')
    dp.callback_query.register(shops.select_remove_shop, RemoveShop.filter())
    dp.callback_query.register(shops.remove_shops, F.data == 'removeShops')
    # Прикрепить магазин контакту
    dp.callback_query.register(shops.select_org, F.data == 'add_shop')
    dp.callback_query.register(shops.select_country, Org.filter(), Contact.menu)
    dp.callback_query.register(shops.select_city, Country.filter(), Contact.menu)
    dp.callback_query.register(shops.start_add_shop, City.filter(), Contact.menu)
    dp.callback_query.register(shops.select_add_shop, AddShop.filter())
    dp.callback_query.register(shops.add_shops, F.data == 'addShops')
    # Изменить стоимость курса у одного магазина
    dp.callback_query.register(shops.select_currency_price_shop, F.data == 'currency_price_shop')
    dp.callback_query.register(shops.enter_new_price, CurrencyOneShop.filter())
    dp.message.register(shops.chage_currency_price_one_shop, OneShopCurrency.price)
    # endregion
    try:
        await dp.start_polling(bot)
    except aiogram.exceptions.TelegramNetworkError:
        dp.callback_query.register(get_start)
    except Exception as e:
        logger.exception(e)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(start())
