import asyncio
import datetime
import json
from collections import namedtuple
from operator import attrgetter

from core.database.ramarket_shop.db_shop import get_counts_shop_sales
from core.oneC.api import Api
from core.oneC.pd_model import User

api = Api()


async def get_employeeInfo(phone):
    return await api.get_client_info(phone)

async def get_employeeInfo_agent_id(agent_id: str):
    response, all_users = await api.get_all_users()
    return [user for user in all_users if user['id'] == agent_id][0]


async def get_shop_name(phone, shop_id):
    for shop in (await api.get_client_info(phone))['Магазины']:
        if shop['idМагазин'] == shop_id:
            return shop['Магазин']


async def get_user_shops(phone):
    """
    :param phone: Сотовый
    :return: Список магазинов прикреплённых пользователю
    """
    phone = str(phone)
    employee = await get_employeeInfo(phone)
    shops = [shop['idМагазин'] for shop in employee['Магазины']]
    response, all_shops = await api.get_all_shops()
    turple = namedtuple('Shop',
                        'name code org_id currency currency_price city city_code country country_code contract contract_id')
    admin_shops = []
    for shop_id in shops:
        for shop in all_shops:
            if shop['id'] == shop_id:
                admin_shops.append(
                    turple(shop['Наименование'], shop['id'], shop['Org'], shop['Валюта'], shop['ВалютаКурс'],
                           shop['Город'], shop['КодГород'], shop['Страна'], shop['КодСтраны'],
                           shop['Договор'], shop['ДоговорID']))
    return admin_shops


async def get_shops_by_agent_id(agent_id):
    """
    Возвращает список магазинов приклеплённых пользователю
    :param agent_id: ID пользователя 1С
    :return: namedtuple('Shop', 'name code org_id currency currency_price city city_code country country_code contract contract_id')
    """
    response, all_users = await api.get_all_users()
    response, all_shops = await api.get_all_shops()
    user_shops = [user['Магазины'] for user in all_users if user['id'] == agent_id][0]
    user_shops = [shop for user_shop in user_shops for shop in all_shops if shop['id'] == user_shop['idМагазин']]
    turple = namedtuple('Shop',
                        'name code org_id currency currency_price city city_code country country_code contract contract_id')
    result_shops = []
    for shop in user_shops:
        result_shops.append(
            turple(shop['Наименование'], shop['id'], shop['Org'], shop['Валюта'], shop['ВалютаКурс'], shop['Город'],
                   shop['КодГород'], shop['Страна'], shop['КодСтраны'],
                   shop['Договор'], shop['ДоговорID']))
    return result_shops


async def get_orgs():
    """
    Возвращает организации
    :return: Возвращает namedtuple('Org', 'name code')
    """
    orgs = []
    turple = namedtuple('Org', 'name code')
    response, all_orgs = await api.get_all_orgs()
    for org in all_orgs:
        if org['ИНН'] not in [i.code for i in orgs]:
            orgs.append(turple(org["Наименование"], org['ИНН']))
    return orgs


async def get_unique_countryes(org_id=None):
    """
    Возвращает уникальные страны
    :param org_id: ID организации
    :return: Возвращает namedtuple('Country', 'name code')
    """
    if org_id is None:
        org_id = False
    countryes = []
    turple = namedtuple('Country', 'name code')
    response, all_shops = await api.get_all_shops()
    for shop in all_shops:
        if org_id:
            if shop['Org'] != org_id:
                continue

        if shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue

        if not shop['КодГород'] or not shop["КодСтраны"]:
            continue

        if shop['КодСтраны'] not in [i.code for i in countryes]:
            countryes.append(turple(shop["Страна"], shop['КодСтраны']))

    return countryes


async def get_unique_cities(org_id):
    """
    Возвращает уникальные города
    :param org_id: ID организации
    :return: Возвращает namedtuple('City', 'name code')
    """
    cities = []
    turple = namedtuple('City', 'name code')
    response, all_shops = await api.get_all_shops()
    for shop in all_shops:
        if shop['Org'] != org_id:
            continue
        if shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        if not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        elif shop['КодГород'] not in [i.code for i in cities]:
            cities.append(turple(shop["Город"], shop['КодГород']))
    return cities


async def get_cities_by_country_code(code: str, org_id=None):
    """
    Возвращает города по коду страны
    :param org_id:
    :param code: Код страны
    :return: Возвращает namedtuple('City', 'name code')
    """
    if org_id is None:
        org_id = False
    response, all_shops = await api.get_all_shops()
    cities = []
    turple = namedtuple('City', 'name code')
    for shop in all_shops:
        if org_id:
            if shop['Org'] != org_id:
                continue
        if shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        if not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        if shop['КодСтраны'] == code and shop['КодГород'] not in [i.code for i in cities]:
            cities.append(turple(shop["Город"], shop['КодГород']))
    return cities


async def get_shops_by_city_code_and_org_id(code: str, org_id, days_sort=14):
    """
    Возвращает магазины по коду города
    :param days_sort:
    :param org_id: ID организации
    :param code: Код страны
    :return: Возвращает namedtuple('Shop', 'name code org_id')
    """
    response, all_shops = await api.get_all_shops()
    shops = []
    Shop = namedtuple('Shop',
                      'name code org_id currency currency_price city city_code country country_code contract contract_id')
    for shop in all_shops:
        if shop["Org"] != org_id:
            continue
        elif shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        elif not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        if shop['КодГород'] == code and shop['КодГород'] not in (i.code for i in shops):
            shops.append(
                Shop(shop['Наименование'], shop['id'], shop['Org'], shop['Валюта'], shop['ВалютаКурс'], shop['Город'],
                     shop['КодГород'], shop['Страна'], shop['КодСтраны'],
                     shop['Договор'], shop['ДоговорID']))

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    week = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=days_sort), '%Y-%m-%d')
    Shop_count = namedtuple('Shop_count',
                            'name code count org_id currency currency_price city city_code country country_code contract contract_id')
    result = []
    for shop in shops:
        count = await get_counts_shop_sales(shop.code, week, today)
        if count:
            result.append(
                Shop_count(shop.name, shop.code, count, shop.org_id, shop.currency, shop.currency_price, shop.city,
                           shop.city_code, shop.country, shop.country_code, shop.contract,
                           shop.contract_id))
        else:
            result.append(
                Shop_count(shop.name, shop.code, 0, shop.org_id, shop.currency, shop.currency_price, shop.city,
                           shop.city_code, shop.country, shop.country_code, shop.contract,
                           shop.contract_id))
    result = sorted(result, key=attrgetter('count'), reverse=True)
    return result


async def get_city_by_code(code: str):
    """
    Возвращает город по коду города
    :param code: Код города
    :return: Возвращает namedtuple('City', 'name code')
    """
    response, all_shops = await api.get_all_shops()
    turple = namedtuple('City', 'name code')
    for shop in all_shops:
        if shop['КодГород'] == code:
            return turple(shop["Город"], shop['КодГород'])


async def get_country_by_code(code: str):
    """
    Возвращает страну по коду страны
    :param code: Код страны
    :return: Возвращает namedtuple('City', 'name code')
    """
    response, all_shops = await api.get_all_shops()
    turple = namedtuple('Country', 'name code')
    for shop in all_shops:
        if shop['КодСтраны'] == code:
            return turple(shop["Страна"], shop['КодСтраны'])


async def get_shop_by_id(shop_id: str):
    """
    Возвращает магазин по его id
    :param shop_id: id магазина
    :return: Возвращает namedtuple('Shop', 'name id org_id currency currency_price country country_code city city_code')
    """
    response, all_shops = await api.get_all_shops()
    turple = namedtuple('Shop',
                        'name code org_id currency currency_price city city_code country country_code contract contract_id')
    for shop in all_shops:
        if shop['id'] == shop_id:
            return turple(shop['Наименование'], shop['id'], shop['Org'], shop['Валюта'], shop['ВалютаКурс'],
                          shop['Город'], shop['КодГород'], shop['Страна'], shop['КодСтраны'],
                          shop['Договор'], shop['ДоговорID'])


async def get_contracts_by_org(org_id: str):
    contracts = await api.get_all_contracts()
    turple = namedtuple('Contact', 'name id')
    result = []
    for contract in contracts:
        if contract['Org'] == org_id:
            result.append(turple(contract['Наименование'], contract['id']))
    return result


async def get_org_name(org_id: str):
    """
    :param org_id: id организации
    :return: Возвращает Название магазина
    """
    response, all_orgs = await api.get_all_orgs()
    for org in all_orgs:
        if org['ИНН'] == org_id:
            return org['Наименование']


async def get_users_by_shop(shop_id: str) -> list[User]:
    """
    :param shop_id: ID магазина
    :return: Список пользователей
    """
    response, all_users = await api.get_all_users()
    result = []
    for user in all_users:
        for shop in user['Магазины']:
            if shop['idМагазин'] == shop_id:
                user = User.model_validate_json(json.dumps(user))
                result.append(user)
    return result


async def get_user_by_id(user_id: str) -> User:
    response, all_users = await api.get_all_users()
    for user in all_users:
        if user['id'] == user_id:
            return User.model_validate_json(json.dumps(user))


if __name__ == '__main__':
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79934055804').text)
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='905539447374').json())
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79831358491').text)
    # print(asyncio.run(get_admin_shops('79934055804')))
    # a = asyncio.run(get_unique_cities())
    # asyncio.run(get_city_by_country_code('784'))
    # a = asyncio.run(get_unique_countryes('165202396034'))
    # print(a)
    # 80, 5093
    print(asyncio.run(get_shops_by_agent_id('7402575')))
