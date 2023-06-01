import re

import funcy
from funcy import str_join

error_head = f"➖➖➖➖➖🚨ОШИБКА🚨➖➖➖➖➖\n"


async def error_server(status):
    return error_head + f'Сервер не отвечает. Код ответа: {status}'


def error_full_name(name):
    return "{error_head}ФИО состоит из 3 слов, а ваше состоит из {count} слов\n<b>Попробуйте снова.</b>".format(error_head=error_head, count=len(name.split()))

menu = f'Главное меню'
need_reg = 'Вы зашли впервые, нажмите кнопку <b><u>Регистрация</u></b>'

succes_registration = 'Регистрация успешна пройдена'


def phoneNotReg(phone):
    text = error_head + \
           (f'Ваш сотовый "{phone}" не зарегистрирован в системе или вас не назначили <u><b>Администратором</b></u>\n'
            f'Уточните вопрос и попробуйте снова.')
    return text


def phone(phone):
    phone = str_join(sep="", seq=re.findall(r'[0-9]*', phone))
    if re.findall(r'^89', phone):
        return re.sub(r'^89', '79', phone)
    return phone


async def employee_true(employeeInfo, phone):
    shops = [i['Магазин'] for i in employeeInfo["Магазины"]]
    text = (f'ℹ️ <b>Информация о сотруднике:</b>\n'
            f'➖➖➖➖➖➖➖➖➖➖➖\n'
            f'<b>Имя сотрудника</b>: <code>{employeeInfo["Наименование"]}</code>\n'
            f'<b>Сотовый</b>: <code>+{phone}</code>\n'
            f'<b>Магазины</b>: <code>{funcy.str_join(sep=",", seq=shops)}</code>\n')
    return text
