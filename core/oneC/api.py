import asyncio
import json

import aiohttp

import config


class Api:
    def __init__(self):
        self.adress = config.adress

    async def get_client_info(self, phone):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/GetUP", data=str(phone)) as response:
                return await response.json()

    async def create_kontragent(self, data):
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/CreateKontr", data=json.dumps(data)) as response:
                return response, await response.text()

    async def create_shop(self, name, inn, kontragent_id, currency, currency_price, cityCode, countryCode):
        """
        :param countryCode: Код страны
        :param cityCode: Код города
        :param name: Название магазина
        :param inn: ИНН магазина
        :param kontragent_id: id контрагента
        :param currency: Валюта
        :param currency_price: Стоимость валюты
        :return: response: Ответ сервера HTTP, text: Ответ в виде текста от сервера
        """
        data = {"Sklad": name, "Org": inn, "Контр": kontragent_id, "Valut": currency, "KursPrice": currency_price, "KodGorod": cityCode, "KodStrana": countryCode}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/CreateTT", data=json.dumps(data)) as response:
                return response, await response.text()

    async def create_employ(self, name: str, admin: bool, phone: str):
        """
        :param name: ФИО сотрудника
        :param admin: булевое значение
        :param phone: Сотовый сотрудника
        :return: response: Ответ сервера HTTP, text: Ответ в виде текста от сервера
        """
        data = {"Name": name, "Admin": admin, "Tel": phone, "Itemc": []}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/CreateSotr", data=json.dumps(data)) as response:
                return response, await response.text()

    async def update_currency_all(self, currency_name: str, price: str):
        """
        Меняем стоимость курса выбранной валюты у всех магазинов 1С
        :param currency_name: Имя валюты
        :param price: Стоимость валюты
        :return: response: Ответ сервера HTTP, text: Ответ в виде текста от сервера
        """
        data = {'Valut': currency_name, "Kurs": price}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/ChangeKursV", data=json.dumps(data)) as response:
                return response, await response.text()

    async def get_all_shops(self):
        """
        Список всех магазинов в 1С
        :return: JSON
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.adress}/GetTTAll") as response:
                return response, await response.json()

    async def get_all_kontragents(self):
        """
        Список всех контрагентов (владельцев магазинов)
        :return: JSON
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.adress}/GetKontr") as response:
                return await response.json()

    async def user_add_shop(self, user_id: str, shops_id: list):
        """
        Прикрепляем 1 магазин пользователю 1С
        :param user_id: ID юзера 1С
        :param shops_id: ID магазинов
        :return: response: Ответ сервера HTTP, text: Ответ в виде текста от сервера
        """
        async with aiohttp.ClientSession() as session:
            for shop_id in shops_id:
                data = {"User": f"{user_id}", "Sklad": f"{shop_id}", "Oper": 1}
                await session.post(f"{self.adress}/ChangeUserParam", data=json.dumps(data))

    async def user_remove_shop(self, user_id: str, shops_id: list):
        """
        Удаляем 1 магазин из пользователя 1С
        :param user_id: ID юзера 1С
        :param shops_id: ID магазинов
        :return: response: Ответ сервера HTTP, text: Ответ в виде текста от сервера
        """
        async with aiohttp.ClientSession() as session:
            for shop_id in shops_id:
                data = {"User": f"{user_id}", "Sklad": f"{shop_id}", "Oper": 2}
                await session.post(f"{self.adress}/ChangeUserParam", data=json.dumps(data))

    async def change_currency_one_shop(self, shop_id: str, currency_price):
        """
        Меняем стоимость курса у одного магазина
        :param shop_id: ID магазина
        :param currency_price: Стоимость курса
        :return: response: Ответ сервера HTTP, text: Ответ в виде текста от сервера
        """
        data = {"MagKV": [{"Sklad": shop_id, "Kurs": currency_price}, ]}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.adress}/ChangeKursMag", data=json.dumps(data)) as response:
                return response, await response.text()


if __name__ == '__main__':
    print(asyncio.run(Api().create_employ()))