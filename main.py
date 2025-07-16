#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

import asyncio
import os

import aiogram.exceptions
from aiogram import Dispatcher, F, Bot
# from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, ExceptionTypeFilter
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

import config
from core.cron.history_orders import send_email_historyOrders_today
from core.database.model import init_models
from core.database.queryDB import get_admins
from core.handlers import contact, errors_hand
from core.handlers.basic import get_start, video_tutorial, contacts, start_delete_contacts, all_users, \
    start_delete_users, filter_total_orders, \
    create_kontragent, test, start_delete_order, accept_orderID_delete_order, accept_date_delete_order
from core.handlers.callback import select_to_delete_contacts, select_currency, history_one_user_all_days, \
    delete_contacts, functions_shop, select_to_delete_users, delete_users, \
    select_filter_user_history_orders, start_create_kontragent
from core.handlers.states import shops, createShop, addContact, createEmployee, shopOperations
from core.handlers.states.createOstatok import start_create_ost
from core.handlers.states.updateCurrencyPriceAll import get_price, update_price
from core.middlewares.checkReg import CheckRegistrationCallbackMiddleware, CheckRegistrationMessageMiddleware
from core.utils.callbackdata import SavedContact, DeleteContact, CreateEmployee, EmployeeAdmin, Country, City, Shops, \
    Currencyes, Kontragent, RemoveShop, AddShop, CurrencyOneShop, \
    Org, DeleteUsers, HistoryShopOrdersByDays, HistoryUserOrdersByDays, HistoryTotalShops, Contract, SelectOrder, \
    DeleteOrder, CurrencyCreateOst
from core.utils.commands import get_commands, get_commands_admins
from core.utils.states import AddPhone, StatesCreateEmployee, HistoryOrdersShop, CreateShop, UpdateCurrencyPriceAll, \
    Contact, OneShopCurrency, HistoryOrdersUser, HistoryOrdersAll, \
    CreateKontragent, ChangeOrderDate, DeleteOrderState, StateCreateOstatok

from core.handlers.send_cash.send_cash import router as send_cash_router
from core.handlers.states import createOstatok

@logger.catch()
async def start():
    if not os.path.exists(os.path.join(config.dir_path, 'logs')):
        os.makedirs(os.path.join(config.dir_path, 'logs'))
    logger.add(os.path.join(config.dir_path, 'logs', 'debug.log'),
               format="{time} | {level} | {name}:{function}:{line} | {message} | {extra}", )

    bot = Bot(token=config.token, parse_mode='HTML')
    # bot = Bot(token=config.token, default=DefaultBotProperties(parse_mode='HTML'))
    await get_commands(bot)
    admins = await get_admins()
    await get_commands_admins(bot, admins)
    await init_models()

    storage = RedisStorage.from_url(config.redisStorage)
    dp = Dispatcher(storage=storage)

    # CRON
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(send_email_historyOrders_today, trigger='cron', minute=0, hour='9,15,23')
    scheduler.start()

    # Errors handlers
    dp.errors.register(errors_hand.error_total, ExceptionTypeFilter(Exception))
    dp.errors.register(errors_hand.tg_duble_error, ExceptionTypeFilter(aiogram.exceptions.TelegramBadRequest))

    # MiddleWares
    dp.message.middleware(CheckRegistrationMessageMiddleware())
    dp.callback_query.middleware(CheckRegistrationCallbackMiddleware())
    # Команды
    dp.message.register(get_start, Command(commands=['start']))
    dp.message.register(video_tutorial, Command(commands=['help']))
    dp.message.register(contacts, Command(commands=['contacts']))
    dp.message.register(test, Command(commands=['test']))
    dp.message.register(addContact.enter_phone, Command(commands=['add_contact']))
    dp.message.register(start_delete_contacts, Command(commands=['delete_contacts']))
    # Админ команды
    dp.message.register(all_users, Command(commands=['all_users']))
    dp.message.register(start_delete_users, Command(commands=['delete_users']))
    dp.message.register(start_delete_order, Command(commands=['delete_order']))
    dp.message.register(filter_total_orders, Command(commands=['total_orders']))

    # Удаление заказа
    dp.message.register(accept_orderID_delete_order, DeleteOrderState.orderID)
    dp.callback_query.register(accept_date_delete_order, DeleteOrderState.orderID, DeleteOrder.filter())
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
    dp.callback_query.register(shopOperations.select_org, F.data == 'shops_operations')

    # История продаж всех магазинов
    dp.callback_query.register(shopOperations.history_total_shops, HistoryTotalShops.filter())
    dp.callback_query.register(shopOperations.send_history_total_shops_all_days,
                               F.data == 'history_total_shops_all_days')
    dp.callback_query.register(shopOperations.history_period, F.data == 'history_period_total_shops')
    dp.message.register(shopOperations.start_period, HistoryOrdersAll.start_date)
    dp.message.register(shopOperations.end_period, HistoryOrdersAll.end_date)
    # Операция с магазинами
    dp.callback_query.register(shopOperations.select_country, Org.filter(), HistoryOrdersShop.org)
    dp.callback_query.register(shopOperations.select_city, Country.filter(), HistoryOrdersShop.country)
    dp.callback_query.register(shopOperations.select_shop, City.filter(), HistoryOrdersShop.city)
    dp.callback_query.register(shopOperations.select_shop_operations, Shops.filter(), HistoryOrdersShop.shops)
    # -- История продаж
    dp.callback_query.register(shopOperations.select_history_orders, F.data == 'history_orders')
    dp.callback_query.register(shopOperations.send_history_all_days, F.data == 'history_all_days')
    dp.callback_query.register(shopOperations.history_period, F.data == 'history_period_shop')
    dp.message.register(shopOperations.start_period, HistoryOrdersShop.start_date)
    dp.message.register(shopOperations.end_period, HistoryOrdersShop.end_date)
    dp.callback_query.register(shopOperations.history_shop_orders_by_days, HistoryShopOrdersByDays.filter())
    # -- Прикрепить договор
    dp.callback_query.register(shopOperations.select_change_contract, F.data == 'change_contract',
                               HistoryOrdersShop.shops)
    # -- Изменить дату чека
    dp.callback_query.register(shopOperations.get_order_id, F.data == 'change_date_order')
    dp.message.register(shopOperations.accept_order_id, ChangeOrderDate.orderID)
    dp.message.register(shopOperations.msg_accept_new_date, ChangeOrderDate.newDate)
    dp.callback_query.register(shopOperations.change_date_select_order, ChangeOrderDate.orderID, SelectOrder.filter())
    # История продаж по пользователю
    dp.callback_query.register(select_filter_user_history_orders, F.data == 'historyOrdersOneUser')
    dp.callback_query.register(history_one_user_all_days, F.data == 'orders_user_all_days')
    dp.callback_query.register(shopOperations.history_period, F.data == 'history_period_user')
    dp.message.register(shopOperations.start_period, HistoryOrdersUser.start_date)
    dp.message.register(shopOperations.end_period, HistoryOrdersUser.end_date)
    dp.callback_query.register(shopOperations.history_user_orders_by_days, HistoryUserOrdersByDays.filter())
    # Создание магазина
    dp.callback_query.register(createShop.select_kontragent, Currencyes.filter(), CreateShop.currencies)
    dp.callback_query.register(createShop.select_org, Kontragent.filter(), CreateShop.kontragent)
    dp.callback_query.register(createShop.select_contract, Org.filter(), CreateShop.kontragent)
    dp.callback_query.register(createShop.select_country, Contract.filter(), CreateShop.kontragent)
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

    # Создать КонтрАгента
    dp.callback_query.register(start_create_kontragent, F.data == 'startCreateKontrAgent')
    dp.message.register(create_kontragent, CreateKontragent.name)

    # Создать остаток
    dp.callback_query.register(createOstatok.start_create_ost, F.data == 'create_ostatok')
    dp.message.register(createOstatok.accept_amount, StateCreateOstatok.amount)
    dp.callback_query.register(createOstatok.confirm_createOst, CurrencyCreateOst.filter())
    dp.callback_query.register(createOstatok.created_createOst, F.data == 'confirm_createOst')


    # Routers
    dp.include_router(send_cash_router)
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
