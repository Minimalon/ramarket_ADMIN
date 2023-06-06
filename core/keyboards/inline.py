from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.oneC.api import Api
from core.utils.callbackdata import *

oneC = Api()


def getKeyboard_start():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Изменить стоимость курса', callback_data='changeCurrencyPrice')
    keyboard.button(text='Создать магазин', callback_data='startCreateShop')
    keyboard.button(text='История продаж магазина', callback_data='historyOrders')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_contacts(contacts):
    keyboard = InlineKeyboardBuilder()
    if contacts:
        for contact in contacts:
            name = (await oneC.get_client_info(contact))['Наименование']
            keyboard.button(text=name, callback_data=SavedContact(phone=contact))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_contact_true():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Операции с магазинами', callback_data='storeFunctions')
    keyboard.button(text='История продаж', callback_data='historyOrdersOneUser')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_contact_false(phone):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Создать сотрудника', callback_data=CreateEmployee(phone=phone))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_select_admin():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Да', callback_data=EmployeeAdmin(admin=True))
    keyboard.button(text='Нет', callback_data=EmployeeAdmin(admin=False))
    keyboard.adjust(2, repeat=True)
    return keyboard.as_markup()


def getKeyboad_select_countries(countries):
    keyboard = InlineKeyboardBuilder()
    for country in countries:
        keyboard.button(text=country.name, callback_data=Country(code=country.code))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboad_select_cities(cities):
    keyboard = InlineKeyboardBuilder()
    for city in cities:
        keyboard.button(text=city.name, callback_data=City(code=city.code))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboad_select_shop(shops):
    keyboard = InlineKeyboardBuilder()
    for shop in shops:
        keyboard.button(text=shop.name, callback_data=Shops(code=shop.code))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_currencies():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='USDV', callback_data=CurrencyAll(currency='USDV'))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_kontragent():
    keyboard = InlineKeyboardBuilder()
    for kontragent in await oneC.get_all_kontragents():
        keyboard.button(text=kontragent['Наименование'], callback_data=Kontragent(id=kontragent['Id']))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_createShop():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Создать магазин', callback_data='createShop')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shop_functions():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Удалить магазин', callback_data='remove_shop')
    keyboard.button(text='Прикрепить магазин', callback_data='add_shop')
    keyboard.button(text='Изменить стоимость курса', callback_data='currency_price_shop')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shop_remove(shops, user_id, removeShop=None):
    if removeShop is None:
        removeShop = []
    keyboard = InlineKeyboardBuilder()
    for shop_name, shop_id in shops:
        if shop_id in removeShop:
            keyboard.button(text=f"{shop_name} ✅", callback_data=RemoveShop(user_id=user_id, shop_id=shop_id))
        elif shop_id not in removeShop:
            keyboard.button(text=shop_name, callback_data=RemoveShop(user_id=user_id, shop_id=shop_id))
    keyboard.button(text="⬅️", callback_data='storeFunctions')
    if len(removeShop) > 0:
        keyboard.button(text="Удалить", callback_data='removeShops')
    keyboard.adjust(2, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shop_add(shops, user_id, addShop=None):
    if addShop is None:
        addShop = []
    keyboard = InlineKeyboardBuilder()
    for shop in shops:
        if shop.code in addShop:
            keyboard.button(text=f"{shop.name} ✅", callback_data=AddShop(user_id=user_id, shop_id=shop.code))
        elif shop.code not in addShop:
            keyboard.button(text=shop.name, callback_data=AddShop(user_id=user_id, shop_id=shop.code))
    keyboard.button(text="⬅️", callback_data='storeFunctions')
    if len(addShop) > 0:
        keyboard.button(text="Прикрепить", callback_data='addShops')
    keyboard.adjust(2, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shop_change_currency_price(data):
    shops = data.get('shops')
    keyboard = InlineKeyboardBuilder()
    for shop_name, shop_id in shops:
        keyboard.button(text=shop_name, callback_data=CurrencyOneShop(shop_id=shop_id))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()
