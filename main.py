#!/usr/bin/env python3.10
# -*- coding: utf-8 -*-

import asyncio
import os

import aiogram.exceptions
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.storage.redis import RedisStorage
from loguru import logger

import config
from core.database.model import init_models
from core.handlers import contact
from core.handlers.basic import get_start, video_tutorial, contacts
from core.handlers.callback import *
from core.handlers.states import shops, createShop, addContact,createEmployee
from core.handlers.states.updateCurrencyPriceAll import get_price, update_price
from core.middlewares.checkReg import CheckRegistrationCallbackMiddleware, CheckRegistrationMessageMiddleware
from core.utils.callbackdata import *
from core.utils.commands import get_commands
from core.utils.states import *


@logger.catch()
async def start():
    if not os.path.exists(os.path.join(config.dir_path, 'logs')):
        os.makedirs(os.path.join(config.dir_path, 'logs'))
    logger.add(os.path.join(config.dir_path, 'logs', 'debug.log'),
               format="{time} | {level} | {name}:{function}:{line} | {message} | {extra}", )

    bot = Bot(token=config.token, parse_mode='HTML')
    await get_commands(bot)
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

    # Сохранённые пользователи
    dp.callback_query.register(contact.get_saved_contact, SavedContact.filter())
    dp.message.register(addContact.add_phone, AddPhone.phone)
    # Регистрация контакта
    dp.message.register(contact.get_contact, F.contact)
    # Создание нового сотрудника
    dp.callback_query.register(createEmployee.select_admin, CreateEmployee.filter())
    dp.callback_query.register(createEmployee.name, EmployeeAdmin.filter())
    dp.message.register(createEmployee.final_create_empliyee, StatesCreateEmployee.name)

    # Главное меню
    dp.callback_query.register(select_currency, F.data == 'changeCurrencyPrice')
    dp.callback_query.register(createShop.select_currency, F.data == 'createShop')

    # Создание магазина
    dp.callback_query.register(createShop.select_kontagent, CurrencyAll.filter(), CreateShop.currencies)
    dp.callback_query.register(createShop.enter_shop_name, Kontragent.filter(), CreateShop.kontragent)
    dp.message.register(createShop.enter_org_inn, CreateShop.name)
    dp.message.register(createShop.enter_shop_currency_price, CreateShop.org)
    dp.message.register(createShop.final, CreateShop.currency_price)
    dp.callback_query.register(createShop.final, CreateShop.currency_price)

    # Изменить стоимость курса у всех магазинов
    dp.callback_query.register(get_price, CurrencyAll.filter())
    dp.message.register(update_price, UpdateCurrencyPriceAll.price)
    # region Действия с полученным контактом
    # Меню
    dp.callback_query.register(functions_shop, F.data == 'storeFunctions')
    # Удалить магазин с контакта
    dp.callback_query.register(shops.start_remove_shop, F.data == 'remove_shop')
    dp.callback_query.register(shops.select_remove_shop, RemoveShop.filter())
    dp.callback_query.register(shops.remove_shops, F.data == 'removeShops')
    # Прикрепить магазин контакту
    dp.callback_query.register(shops.start_add_shop, F.data == 'add_shop')
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
