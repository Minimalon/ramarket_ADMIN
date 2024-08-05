import re

import funcy
import loguru
from funcy import str_join

from core.database.ramarket_shop.db_shop import get_orders_by_1c_id
from core.handlers.send_cash.pd_model import SendCash
from core.oneC.oneC import get_shop_by_id

error_head = f"➖➖➖➖🚨ОШИБКА🚨➖➖➖➖\n"
intersum_head = f"➖➖➖➖❗️ВАЖНО❗️➖➖➖➖\n"
information_head = f"➖➖➖ℹ️Информацияℹ️➖➖➖\n"
auth_head = f"➖➖➖🔑Авторизация🔑➖➖➖\n"
success_head = '➖➖➖✅Успешно✅➖➖➖\n'


async def error_server(status):
    return error_head + f'Сервер не отвечает. Код ответа: {status}'


def error_full_name(name):
    return "{error_head}ФИО состоит из 3 слов, а ваше состоит из {count} слов\n<b>Попробуйте снова.</b>".format(
        error_head=error_head, count=len(name.split()))


menu = f'Главное меню'
need_reg = 'Вы зашли впервые, нажмите кнопку <b><u>Регистрация</u></b>'

succes_registration = 'Регистрация успешна пройдена'


def phoneNotReg(phone):
    text = error_head + \
           (f'Ваш сотовый "{phone}" не зарегистрирован в системе или вас не назначили <u><b>Администратором</b></u>\n'
            f'Уточните вопрос и попробуйте снова.')
    return text


async def employee_true(employeeInfo, phone, admin_info, superadmin):
    admin_shops = [shop['idМагазин'] for shop in admin_info['Магазины']]
    shops = [i['Магазин'] for i in employeeInfo["Магазины"]]
    text = (f'ℹ️ <b>Информация о сотруднике:</b>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'<b>Имя сотрудника</b>: <code>{employeeInfo["Наименование"]}</code>\n'
            f'<b>Сотовый</b>: <code>{phone}</code>\n'
            f'<b>Магазины</b>: <code>{funcy.str_join(sep="|", seq=shops)}</code>\n'
            f'<b>Администратор</b>: <code>{employeeInfo["Администратор"]}</code>\n')

    sales_text = (f'➖➖➖➖➖➖➖➖➖➖➖\n'
                  f'ℹ️ <b>Продажи:</b>\n'
                  f'<b>Сегодня:</b> {len(await get_orders_by_1c_id(employeeInfo["id"], 1))}\n'
                  f'<b>7 дней:</b> {len(await get_orders_by_1c_id(employeeInfo["id"], 7))}\n'
                  f'<b>30 дней:</b> {len(await get_orders_by_1c_id(employeeInfo["id"], 30))}\n'
                  )
    if superadmin:
        text += sales_text
    else:
        for admin_shop in admin_shops:
            if admin_shop in (shop['idМагазин'] for shop in employeeInfo['Магазины']) or superadmin:
                text += sales_text
                break
    return text


def phone(phone):
    phone = str_join(sep="", seq=re.findall(r'[0-9]*', phone))
    if re.findall(r'^89', phone):
        return re.sub(r'^89', '79', phone)
    return phone


async def send_cash(sc: SendCash):
    shop = await get_shop_by_id(sc.shop_id)
    return (
        f"{information_head}"
        f"Валюта: <code>{sc.currency}</code>\n"
        f"Сумма: <code>{sc.amount}</code>\n"
        f"Получатель: <code>{sc.user.name}</code>\n"
        f"Магазин: <code>{shop.name}</code>\n"
    )
