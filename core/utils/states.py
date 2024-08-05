from aiogram.fsm.state import State, StatesGroup


class UpdateCurrencyPriceAll(StatesGroup):
    price = State()


class Contact(StatesGroup):
    menu = State()


class OneShopCurrency(StatesGroup):
    price = State()


class AddPhone(StatesGroup):
    phone = State()


class CreateShop(StatesGroup):
    currencies = State()
    kontragent = State()
    name = State()
    org = State()
    currency_price = State()
    final = State()


class StatesCreateEmployee(StatesGroup):
    admin = State()
    name = State()


class HistoryOrdersShop(StatesGroup):
    org = State()
    country = State()
    city = State()
    shops = State()
    start_date = State()
    end_date = State()


class HistoryOrdersUser(StatesGroup):
    menu = State()
    start_date = State()
    end_date = State()


class HistoryOrdersAll(StatesGroup):
    menu = State()
    start_date = State()
    end_date = State()


class CreateKontragent(StatesGroup):
    name = State()


class ChangeOrderDate(StatesGroup):
    orderID = State()
    newDate = State()


class DeleteOrderState(StatesGroup):
    orderID = State()
    date = State()


class SendCashState(StatesGroup):
    currency = State()
    shop = State()
    user = State()
    amount = State()
