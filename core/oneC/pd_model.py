from pydantic import BaseModel, Field


class Shop(BaseModel):
    name: str = Field('', description="Название магазина", alias="Наименование")
    code: str = Field('', description="Код магазина", alias="id")
    org_id: str = Field('', description="ID организации", alias="Org")
    currency: str = Field('', description="Валюта", alias="Валюта")
    currency_price: str | float = Field(0, description="Стоимость валюты", alias="ВалютаКурс")
    city: str = Field('', description="Город", alias="Город")
    city_code: str = Field('', description="Код города", alias="КодГород")
    country: str = Field('', description="Страна", alias="Страна")
    country_code: str = Field('', description="Код страны", alias="КодСтраны")
    contract: str = Field('', description="Договор", alias="Договор")
    contract_id: str = Field('', description="ID договора", alias="ДоговорID")


class User(BaseModel):
    name: str = Field('', description="Название пользователя", alias="Наименование")
    id: str = Field('', description="ID пользователя", alias="id")
    admin: str = Field('', description="Админ", alias="Админ")
    pravoRKO: str = Field('', description="Админ", alias="ПравоРКО")
    phone: str = Field('', description="Телефон", alias="Телефон")
    shops: list[Shop] = Field(description="Магазины", alias="Магазины")

class ShopBalance(BaseModel):
    shop_id: str = Field(alias='Магазин')
    shop_name: str = Field(alias='Наименование')
    currency: str = Field(alias='Валюта')
    balance: int = Field(alias='СостояниеРасчетов')

class CreateOstatok(BaseModel):
    shop_id: str = Field(alias='Shop')
    amount: str = Field(alias='Amount')
    user_id: str = Field(alias='User')
    currency: str = Field(alias='Currency')
    currency_price: str = Field(alias='KursPrice')

class CreateRKO(BaseModel):
    shop_id: str = Field(alias='Shop')
    amount: str = Field(alias='Amount')
    user_id: str = Field(alias='User')
    currency: str = Field(alias='Currency')
    currency_price: str = Field(alias='KursPrice')