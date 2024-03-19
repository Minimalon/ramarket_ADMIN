from datetime import timedelta

from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.database.ramarket_shop.model import HistoryOrders
from core.oneC.api import Api
from core.utils.callbackdata import *

oneC = Api()


def getKeyboard_start():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Изменить стоимость курса', callback_data='changeCurrencyPrice')
    keyboard.button(text='Создать магазин', callback_data='startCreateShop')
    keyboard.button(text='Создать контрагента', callback_data='startCreateKontrAgent')
    keyboard.button(text='Операции с магазином', callback_data='shops_operations')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shops_operations():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='История продаж', callback_data='history_orders')
    keyboard.button(text='Изменить договор', callback_data='change_contract')
    keyboard.button(text='Изменить дату чека', callback_data='change_date_order')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_contacts(contacts):
    keyboard = InlineKeyboardBuilder()
    if contacts:
        for contact in contacts:
            try:
                name = (await oneC.get_client_info(contact))['Наименование']
                keyboard.button(text=name, callback_data=SavedContact(phone=contact))
            except TypeError:
                keyboard.button(text=f"{contact} Удалён из базы 1С", callback_data=SavedContact(phone=contact))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_filters_user_history_orders():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Сегодня', callback_data=HistoryUserOrdersByDays(days=0))
    keyboard.button(text='7 дней', callback_data=HistoryUserOrdersByDays(days=7))
    keyboard.button(text='30 дней', callback_data=HistoryUserOrdersByDays(days=30))
    keyboard.button(text='За всё время', callback_data='orders_user_all_days')
    keyboard.button(text='Промежуток времени', callback_data='history_period_user')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_filters_history_orders():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Сегодня', callback_data=HistoryShopOrdersByDays(days=0))
    keyboard.button(text='7 дней', callback_data=HistoryShopOrdersByDays(days=7))
    keyboard.button(text='30 дней', callback_data=HistoryShopOrdersByDays(days=30))
    keyboard.button(text='За всё время', callback_data='history_all_days')
    keyboard.button(text='Промежуток времени', callback_data='history_period_shop')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_contracts(contracts):
    keyboard = InlineKeyboardBuilder()
    if contracts:
        for contract in contracts:
            keyboard.button(text=contract.name, callback_data=Contract(id=contract.id))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_filters_total_shop_history_orders():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Сегодня', callback_data=HistoryTotalShops(days=0))
    keyboard.button(text='7 дней', callback_data=HistoryTotalShops(days=7))
    keyboard.button(text='30 дней', callback_data=HistoryTotalShops(days=30))
    keyboard.button(text='За всё время', callback_data='history_total_shops_all_days')
    keyboard.button(text='Промежуток времени', callback_data='history_period_total_shops')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_start_delete_users(contacts):
    keyboard = InlineKeyboardBuilder()
    if contacts:
        for count, contact in enumerate(contacts, start=1):
            keyboard.button(text=f"№{count} {contact['Наименование']} 📱{contact['Телефон'][-7:]}", callback_data=DeleteUsers(id=contact['id']))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_all_contacts(contacts):
    keyboard = InlineKeyboardBuilder()
    if contacts:
        for count, contact in enumerate(contacts, start=1):
            keyboard.button(text=f'№{count} {contact.name} 📱{contact.phone[-7:]} | {contact.count_total_orders}', callback_data=SavedContact(phone=contact.phone))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_delete_users(contacts, to_delete=None):
    if not to_delete:
        to_delete = []
    keyboard = InlineKeyboardBuilder()
    if contacts:
        for count, contact in enumerate(contacts, start=1):
            if contact['id'] in to_delete:
                keyboard.button(text=f"№{count} {contact['Наименование']} 📱{contact['Телефон'][-7:]}✅", callback_data=DeleteUsers(id=contact["id"]))
            else:
                keyboard.button(text=f"№{count} {contact['Наименование']} 📱{contact['Телефон'][-7:]}", callback_data=DeleteUsers(id=contact["id"]))
    if len(to_delete) > 0:
        keyboard.button(text="Удалить 🗑", callback_data='deleteUsers')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


async def getKeyboard_delete_contacts(contacts, to_delete=None):
    if not to_delete:
        to_delete = []
    keyboard = InlineKeyboardBuilder()
    if contacts:
        for contact in contacts:
            try:
                name = (await oneC.get_client_info(contact))['Наименование']
            except TypeError:
                name = contact
            if contact in to_delete:
                keyboard.button(text=f'{name} ✅', callback_data=DeleteContact(phone=contact))
            else:
                keyboard.button(text=name, callback_data=DeleteContact(phone=contact))
    if len(to_delete) > 0:
        keyboard.button(text="Удалить 🗑", callback_data='deleteContacts')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_contact_true(superadmin: bool, employee_info, admin_info):
    keyboard = InlineKeyboardBuilder()
    employee_admin = True if employee_info['Администратор'] == 'Да' else False
    admin_shops = [shop['idМагазин'] for shop in admin_info['Магазины']]
    if superadmin or not employee_admin:
        keyboard.button(text='Операции с магазинами', callback_data='storeFunctions')
    if superadmin:
        keyboard.button(text='История продаж', callback_data='historyOrdersOneUser')
    else:
        for admin_shop in admin_shops:
            if admin_shop in (shop['idМагазин'] for shop in employee_info['Магазины']) or superadmin:
                keyboard.button(text='История продаж', callback_data='historyOrdersOneUser')
                break
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


def getKeyboad_orgs(orgs):
    keyboard = InlineKeyboardBuilder()
    for org in orgs:
        keyboard.button(text=org.name, callback_data=Org(code=org.code))
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
        keyboard.button(text=f"{shop.name} {shop.contract}", callback_data=Shops(code=shop.code, org_id=shop.org_id))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_currencies():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='USD', callback_data=Currencyes(currency='USDV'))
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
    # keyboard.button(text='Изменить стоимость курса', callback_data='currency_price_shop')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shop_remove(shops, user_id, removeShop=None):
    if removeShop is None:
        removeShop = []
    keyboard = InlineKeyboardBuilder()
    for shop in shops:
        if shop.code in removeShop:
            keyboard.button(text=f"{shop.name} {shop.contract} ✅", callback_data=RemoveShop(user_id=user_id, shop_id=shop.code))
        elif shop.code not in removeShop:
            keyboard.button(text=f"{shop.name} {shop.contract}", callback_data=RemoveShop(user_id=user_id, shop_id=shop.code))
    keyboard.button(text="⬅️", callback_data='storeFunctions')
    if len(removeShop) > 0:
        keyboard.button(text="Удалить", callback_data='removeShops')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shop_add(shops, user_id, addShop=None):
    if addShop is None:
        addShop = []
    keyboard = InlineKeyboardBuilder()
    for shop in shops:
        if shop.code in addShop:
            keyboard.button(text=f"{shop.name} {shop.contract} ✅", callback_data=AddShop(user_id=user_id, shop_id=shop.code))
        elif shop.code not in addShop:
            keyboard.button(text=f"{shop.name} {shop.contract}", callback_data=AddShop(user_id=user_id, shop_id=shop.code))
    keyboard.button(text="⬅️", callback_data='storeFunctions')
    if len(addShop) > 0:
        keyboard.button(text="Прикрепить", callback_data='addShops')
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def getKeyboard_shop_change_currency_price(data):
    shops = data.get('shops')
    keyboard = InlineKeyboardBuilder()
    for shop_name, shop_id in shops:
        keyboard.button(text=shop_name, callback_data=CurrencyOneShop(shop_id=shop_id))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()


def kb_select_order(orders: list[HistoryOrders]):
    keyboard = InlineKeyboardBuilder()
    for order in orders:
        date = order.date + timedelta(hours=3)
        keyboard.button(text=f'{date.strftime("%d.%m.%Y %H:%M:%S")} | {order.order_id}',
                        callback_data=SelectOrder(
                            order_id=order.order_id,
                            date=date.strftime('%Y%m%d%H%M%S'),
                            shop_id=str(order.shop_id),
                        ))
    keyboard.adjust(1, repeat=True)
    return keyboard.as_markup()
