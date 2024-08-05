import json

from loguru import logger

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import config
from core.database.queryDB import get_client_info
from core.handlers.send_cash.pd_model import SendCash
from core.keyboards import inline
from core.oneC.oneC import get_user_shops, get_user_by_id, get_users_by_shop
from core.utils import texts
from core.utils.callbackdata import SendCashCurrency, SendCashShop, SendCashUser
from core.utils.states import SendCashState

router = Router()


@router.callback_query(F.data == 'send_cash')
async def select_valut(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Выдача наличных"')
    await call.message.edit_text("Выберите валюту", reply_markup=inline.kb_send_cash_select_currency())
    await state.set_state(SendCashState.currency)


@router.callback_query(SendCashState.currency, SendCashCurrency.filter())
async def select_shop(call: CallbackQuery, callback_data: SendCashCurrency, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал валюту "{callback_data.currency}"')
    client_info = await get_client_info(call.message.chat.id)
    shops = await get_user_shops(client_info.phone_number)
    if not shops:
        await call.message.edit_text(texts.error_head + 'У вас не привязано ни одного магазина')
        log.error('У вас не привязано ни одного магазина')

    sc = SendCash(currency=callback_data.currency)
    await state.update_data(send_cash=sc.model_dump_json(by_alias=True))
    await call.message.edit_text("Выберите магазин", reply_markup=inline.kb_send_cash_select_shop(shops))
    await state.set_state(SendCashState.shop)


@router.callback_query(SendCashState.shop, SendCashShop.filter())
async def select_user(call: CallbackQuery, callback_data: SendCashShop, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал магазин "{callback_data.shop_id}"')
    data = await state.get_data()
    sc = SendCash.model_validate_json(data.get('send_cash'))
    sc.shop_id = callback_data.shop_id
    users = await get_users_by_shop(callback_data.shop_id)
    if not users:
        await call.message.edit_text(texts.error_head + 'У магазина нет ни одного пользователя')
        log.error('У магазина нет ни одного пользователя')
    await state.update_data(send_cash=sc.model_dump_json(by_alias=True))
    await call.message.edit_text("Выберите получателя", reply_markup=inline.kb_send_cash_select_user(users))
    await state.set_state(SendCashState.user)


@router.callback_query(SendCashState.user, SendCashUser.filter())
async def select_amount(call: CallbackQuery, callback_data: SendCashUser, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрал получателя "{callback_data.id}"')
    data = await state.get_data()
    sc = SendCash.model_validate_json(data.get('send_cash'))
    sc.user = await get_user_by_id(callback_data.id)
    await state.update_data(send_cash=sc.model_dump_json(by_alias=True))
    await call.message.edit_text("Укажите сумму")
    await state.set_state(SendCashState.amount)


@router.message(SendCashState.amount)
async def accept_amount(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info(f'Указал сумму "{message.text}"')
    data = await state.get_data()
    sc = SendCash.model_validate_json(data.get('send_cash'))
    sc.amount = float(message.text)
    await state.update_data(send_cash=sc.model_dump_json(by_alias=True))
    await message.answer(await texts.send_cash(sc),
                         reply_markup=inline.kb_send_cash_confirm())


@router.callback_query(F.data == 'send_cash_confirm')
async def send_cash_confirm(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали "Отправить"')
    data = await state.get_data()
    sc = SendCash.model_validate_json(data.get('send_cash'))
    if config.develope_mode:
        await call.message.answer(json.dumps(sc.send_to_1c()))
    else:
        await call.answer('Данная кнопка в разработке')
