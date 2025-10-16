import json

from loguru import logger

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import config
from core.database.queryDB import get_client_info
from core.handlers.send_cash.pd_model import CreateOstatok
from core.keyboards import inline
from core.oneC.api import Api
from core.oneC.oneC import get_user_shops, get_user_by_id, get_users_by_shop, get_shop_by_id
from core.utils import texts
from core.utils.callbackdata import CreateOstatokCurrency, CreateOstatokShop, CreateOstatokUser
from core.utils.states import CreateOstatokState

router = Router()


@router.callback_query(F.data == 'create_ostatok')
async def select_valut(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Создать остаток"')
    await call.message.edit_text("Выберите валюту", reply_markup=inline.kb_create_ostatok_select_currency())
    await state.set_state(CreateOstatokState.currency)


@router.callback_query(CreateOstatokState.currency, CreateOstatokCurrency.filter())
async def select_shop(call: CallbackQuery, callback_data: CreateOstatokCurrency, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал валюту "{callback_data.currency}"')
    client_info = await get_client_info(call.message.chat.id)
    shops = await get_user_shops(client_info.phone_number)
    if not shops:
        await call.message.edit_text(texts.error_head + 'У вас не привязано ни одного магазина')
        log.error('У вас не привязано ни одного магазина')

    sc = CreateOstatok(currency=callback_data.currency)
    await state.update_data(create_ostatok=sc.model_dump_json(by_alias=True))
    await call.message.edit_text("Выберите магазин", reply_markup=inline.kb_create_ostatok_select_shop(shops))
    await state.set_state(CreateOstatokState.shop)


@router.callback_query(CreateOstatokState.shop, CreateOstatokShop.filter())
async def select_user(call: CallbackQuery, callback_data: CreateOstatokShop, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал магазин "{callback_data.shop_id}"')
    data = await state.get_data()
    sc = CreateOstatok.model_validate_json(data.get('create_ostatok'))
    sc.shop_id = callback_data.shop_id
    users = await get_users_by_shop(callback_data.shop_id)
    if not users:
        await call.message.edit_text(texts.error_head + 'У магазина нет ни одного пользователя')
        log.error('У магазина нет ни одного пользователя')
    await state.update_data(create_ostatok=sc.model_dump_json(by_alias=True))
    await call.message.edit_text("Выберите получателя", reply_markup=inline.kb_create_ostatok_select_user(users))
    await state.set_state(CreateOstatokState.user)


@router.callback_query(CreateOstatokState.user, CreateOstatokUser.filter())
async def select_amount(call: CallbackQuery, callback_data: CreateOstatokUser, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал получателя "{callback_data.id}"')
    data = await state.get_data()
    sc = CreateOstatok.model_validate_json(data.get('create_ostatok'))
    sc.user = await get_user_by_id(callback_data.id)
    await state.update_data(create_ostatok=sc.model_dump_json(by_alias=True))
    await call.message.edit_text("Укажите сумму")
    await state.set_state(CreateOstatokState.amount)


@router.message(CreateOstatokState.amount)
async def accept_amount(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info(f'Указал сумму "{message.text}"')
    data = await state.get_data()
    sc = CreateOstatok.model_validate_json(data.get('create_ostatok'))
    sc.amount = message.text
    await state.update_data(create_ostatok=sc.model_dump_json(by_alias=True))
    await message.answer(await texts.send_cash(sc),
                         reply_markup=inline.kb_send_cash_confirm())


@router.callback_query(F.data == 'create_ostatok_confirm')
async def send_cash_confirm(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Отправить"')
    data = await state.get_data()
    sc = CreateOstatok.model_validate_json(data.get('create_ostatok'))
    api = Api()
    response, text = await api.create_ostatok(sc.shop_id, sc.amount, sc.currency, sc.user.id)
    shop = await get_shop_by_id(sc.shop_id)
    if response.ok:
        await call.message.edit_text(texts.success_head + f'Cоздан остаток\n\n - Магазин "{shop.name}"\n - Сумма {sc.amount} {sc.currency}')
    else:
        await call.message.edit_text(texts.error_head + text)
    await state.clear()
