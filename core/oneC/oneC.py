import asyncio
import datetime
from collections import namedtuple
from operator import attrgetter

import requests

from core.database.ramarket_shop.db_shop import get_counts_shop_sales
from core.oneC.api import Api

api = Api()


async def get_employeeInfo(phone):
    return await api.get_client_info(phone)


async def get_shop_name(phone, shop_id):
    for shop in (await api.get_client_info(phone))['Магазины']:
        if shop['idМагазин'] == shop_id:
            return shop['Магазин']


async def get_admin_shops(phone):
    phone = str(phone)
    employee = await get_employeeInfo(phone)
    shops = [shop['idМагазин'] for shop in employee['Магазины']]
    response, all_shops = await api.get_all_shops()
    turple = namedtuple('Shop', 'name code')
    admin_shops = []
    for shop_id in shops:
        for shop in all_shops:
            if shop['id'] == shop_id:
                admin_shops.append(turple(shop['Наименование'], shop['id']))
    return admin_shops


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
    :return: Возвращает namedtuple('Shop', 'name code')
    """
    response, all_shops = await api.get_all_shops()
    shops = []
    Shop = namedtuple('Shop', 'name code')
    for shop in all_shops:
        if shop["Org"] != org_id:
            continue
        elif shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        elif not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        if shop['КодГород'] == code and shop['КодГород'] not in (i.code for i in shops):
            shops.append(Shop(shop["Наименование"], shop['id']))

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    week = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(days=days_sort), '%Y-%m-%d')
    Shop_count = namedtuple('Shop_count', 'name code count')
    result = []
    for shop in shops:
        count = await get_counts_shop_sales(shop.code, week, today)
        if count:
            result.append(Shop_count(shop.name, shop.code, count))
        else:
            result.append(Shop_count(shop.name, shop.code, 0))
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
    :return: Возвращает namedtuple('Shop', 'name id currency currency_price country country_code city city_code')
    """
    response, all_shops = await api.get_all_shops()
    turple = namedtuple('Shop', 'name id currency currency_price country country_code city city_code')
    for shop in all_shops:
        if shop['id'] == shop_id:
            return turple(shop["Наименование"], shop['id'], shop['Валюта'], shop['ВалютаКурс'], shop['Страна'], shop['КодСтраны'], shop['Город'], shop['КодГород'])


async def get_org_name(org_id: str):
    """
    :param org_id: id организации
    :return: Возвращает Название магазина
    """
    response, all_orgs = await api.get_all_orgs()
    for org in all_orgs:
        if org['ИНН'] == org_id:
            return org['Наименование']


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
    print(asyncio.run(get_shops_by_city_code_and_org_id('000000004', '1603007671')))
