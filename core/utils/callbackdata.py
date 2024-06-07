from aiogram.filters.callback_data import CallbackData


class EmployeeAdmin(CallbackData, prefix='employeeAdmin'):
    admin: bool


class CreateEmployee(CallbackData, prefix='employee'):
    phone: str


class Currencyes(CallbackData, prefix='currencyAll'):
    currency: str


class RemoveShop(CallbackData, prefix='rm_shop'):
    shop_id: str
    user_id: str


class AddShop(CallbackData, prefix='add_shop'):
    shop_id: str
    user_id: str


class CurrencyOneShop(CallbackData, prefix='currency_one_shop'):
    shop_id: str


class Kontragent(CallbackData, prefix='kontragent'):
    id: str


class SavedContact(CallbackData, prefix='savedContact'):
    phone: str


class DeleteUsers(CallbackData, prefix='deleteUsers'):
    id: str


class DeleteContact(CallbackData, prefix='deleteContact'):
    phone: str


class Country(CallbackData, prefix='country'):
    code: str


class City(CallbackData, prefix='city'):
    code: str


class Org(CallbackData, prefix='org'):
    code: str


class Shops(CallbackData, prefix='shops'):
    code: str
    org_id: str


class HistoryShopOrdersByDays(CallbackData, prefix='historyOrdersShopByDays'):
    days: int


class HistoryUserOrdersByDays(CallbackData, prefix='historyOrdersUserByDays'):
    days: int


class HistoryTotalShops(CallbackData, prefix='historyTotalShops'):
    days: int


class Contract(CallbackData, prefix='contract'):
    id: str


class Year(CallbackData, prefix='Year'):
    Year: str


class Month(CallbackData, prefix='Month'):
    Month: str


class Day(CallbackData, prefix='Day'):
    Day: str


class SelectOrder(CallbackData, prefix='select_order'):
    order_id: str
    date: str  # %Y%m%d%H%M%S
    shop_id: str


class DeleteOrder(CallbackData, prefix='delete_order'):
    order_id: str
    date: str  # %Y%m%d%H%M
    shop_id: str
