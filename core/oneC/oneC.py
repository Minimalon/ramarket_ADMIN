import asyncio
from collections import namedtuple

from core.oneC.api import Api

api = Api()


async def get_employeeInfo(phone):
    return await api.get_client_info(phone)


async def get_shop_name(phone, shop_id):
    for shop in (await api.get_client_info(phone))['Магазины']:
        if shop['idМагазин'] == shop_id:
            return shop['Магазин']


async def get_unique_countryes():
    """
    Возвращает уникальные страны
    :return: Возвращает namedtuple('Country', 'name code')
    """
    countryes = []
    turple = namedtuple('Country', 'name code')
    response, all_shops = await api.get_all_shops()
    for shop in all_shops:
        if shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        if not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        elif shop['КодСтраны'] not in [i.code for i in countryes]:
            countryes.append(turple(shop["Страна"], shop['КодСтраны']))
    return countryes


async def get_unique_cities():
    """
    Возвращает уникальные города
    :return: Возвращает namedtuple('City', 'name code')
    """
    cities = []
    turple = namedtuple('City', 'name code')
    response, all_shops = await api.get_all_shops()
    for shop in all_shops:
        if shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        if not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        elif shop['КодГород'] not in [i.code for i in cities]:
            cities.append(turple(shop["Город"], shop['КодГород']))
    return cities


async def get_cities_by_country_code(code: str):
    """
    Возвращает города по коду страны
    :param code: Код страны
    :return: Возвращает namedtuple('City', 'name code')
    """
    response, all_shops = await api.get_all_shops()
    cities = []
    turple = namedtuple('City', 'name code')
    for shop in all_shops:
        if shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        if not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        if shop['КодСтраны'] == code and shop['КодГород'] not in [i.code for i in cities]:
            cities.append(turple(shop["Город"], shop['КодГород']))
    return cities


async def get_shops_by_city_code(code: str):
    """
    Возвращает магазины по коду города
    :param code: Код страны
    :return: Возвращает namedtuple('Shop', 'name code')
    """
    response, all_shops = await api.get_all_shops()
    shops = []
    turple = namedtuple('Shop', 'name code')
    for shop in all_shops:
        if shop['Город'] == "Удалить" or shop['Страна'] == "Удалить":
            continue
        if not shop['КодГород'] or not shop["КодСтраны"]:
            continue
        if shop['КодГород'] == code and shop['КодГород'] not in (i.code for i in shops):
            shops.append(turple(shop["Наименование"], shop['id']))
    return shops


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




if __name__ == '__main__':
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79934055804').text)
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='905539447374').json())
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79831358491').text)
    # asyncio.run(get_unique_countryes())
    a = asyncio.run(get_unique_cities())
    # asyncio.run(get_city_by_country_code('784'))
    # a = asyncio.run(get_shops_by_city_code('000000003'))
    print(a)
    # 80, 5093
