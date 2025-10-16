from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from core.database.queryDB import get_client_info
from core.keyboards.inline import kb_createOst_currency, kb_createOst_confirm
from core.oneC.api import Api
from core.oneC.oneC import get_shop_by_id, get_user_by_phone
from core.oneC.pd_model import CreateOstatok
from core.utils import texts
from core.utils.callbackdata import CurrencyCreateOst
from core.utils.states import StateCreateOstatok

oneC = Api()


async def start_create_ost(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info('Нажали кнопку "Создать остаток"')
    await state.set_state(StateCreateOstatok.amount)
    await call.message.edit_text("Введите сумму")


async def accept_amount(message: Message, state: FSMContext):
    log = logger.bind(name=message.chat.first_name, chat_id=message.chat.id)
    log.info(f'Ввели сумму "{message.text}"')
    try:
        amount = float(message.text)
    except Exception:
        await message.answer(texts.error_head + "Вы ввели не сумму, попробуйте еще раз")
        log.error("Вы ввели не сумму, попробуйте еще раз")
        return
    await state.update_data(createOst_amount=amount)
    await state.set_state(StateCreateOstatok.amount)
    await message.answer("Выберите валюту", reply_markup=kb_createOst_currency())


async def confirm_createOst(call: CallbackQuery, state: FSMContext, callback_data: CurrencyCreateOst):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.info(f'Выбрали валюту "{callback_data.currency}"')
    data = await state.get_data()
    await state.update_data(createOst_currency=callback_data.currency)
    shop_info = await get_shop_by_id(data['shop_id'])
    txt = f"""
{texts.information_head}
Магазин: {shop_info.name}
Сумма: {data['createOst_amount']}
Валюта: {callback_data.currency}
Стоимость курса: {shop_info.currency_price}
    """
    await call.message.edit_text(txt, reply_markup=kb_createOst_confirm())


async def created_createOst(call: CallbackQuery, state: FSMContext):
    log = logger.bind(name=call.message.chat.first_name, chat_id=call.message.chat.id)
    log.success('Успешно создали остаток')
    data = await state.get_data()
    shop_info = await get_shop_by_id(data['shop_id'])
    log.debug(f'Магазин: {shop_info.code} Сумма: {data["createOst_amount"]} Валюта: {data["createOst_currency"]} Стоимость курса: {shop_info.currency_price}')
    user_db = await get_client_info(call.message.chat.id)
    user = await get_user_by_phone(user_db.phone_number)
    txt = f"""
{texts.success_head}
Остаток создан

Магазин: {shop_info.name}
Сумма: {data['createOst_amount']}
Валюта: {data['createOst_currency']}
Стоимость курса: {shop_info.currency_price}
    """

    await oneC.create_ostatok(
            shop=shop_info.code,
            amount=data.get('createOst_amount'),
            currency=data.get('createOst_currency'),
            currency_price=shop_info.currency_price,
            user=user.id,
    )
    await call.message.edit_text(txt)
