from aiogram.filters.callback_data import CallbackData


class EmployeeAdmin(CallbackData, prefix='employeeAdmin'):
    admin: bool


class CreateEmployee(CallbackData, prefix='employee'):
    phone: str


class CurrencyAll(CallbackData, prefix='currencyAll'):
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


class Country(CallbackData, prefix='country'):
    code: str


class City(CallbackData, prefix='city'):
    code: str


class Shops(CallbackData, prefix='shops'):
    code: str
