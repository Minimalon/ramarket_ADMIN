from core.oneC.api import Api
import requests

api = Api()


async def get_employeeInfo(phone):
    return await api.get_client_info(phone)


async def get_shop_name(phone, shop_id):
    for shop in (await api.get_client_info(phone))['Магазины']:
        if shop['idМагазин'] == shop_id:
            return shop['Магазин']

if __name__ == '__main__':
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79934055804').text)
    # print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='905539447374').json())
    print(requests.post('http://pr-egais.ddns.net:24142/RAMA/hs/GetUP', data='79831358491').text)
    # 80, 5093
