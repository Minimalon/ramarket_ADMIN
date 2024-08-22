import enum

from sqlalchemy import String, Column, DateTime, BigInteger, Enum, Float
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

import config

engine = create_async_engine(f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
Base = declarative_base()


class OrderStatus(enum.Enum):
    sale = 1  # Продали
    prepare_delete = 2  # Подготовка к удалению
    delete = 3  # Удалён в лукере
    cancel = 4  # Отменили
    change_date = 5  # Изменили дату в лукере и в бд


class HistoryOrders(Base):
    __tablename__ = 'historyOrders'
    id = Column(BigInteger, nullable=False, primary_key=True)
    date = Column(DateTime(timezone=True), server_default=func.now())
    order_id = Column(String(250), nullable=False)
    chat_id = Column(String(50))
    agent_id = Column(String(50))
    agent_name = Column(String(250))
    rezident = Column(String(50))
    country_code = Column(String(50))
    country_name = Column(String(250))
    city_code = Column(String(50))
    city_name = Column(String(250))
    shop_id = Column(String(50))
    shop_name = Column(String(50))
    shop_currency = Column(String(50))
    paymentGateway = Column(String(50))
    paymentType = Column(String(50))
    payment_name = Column(String(250))
    tax = Column(Float(10))
    product_id = Column(String(50))
    product_name = Column(String(250))
    price = Column(String(50))
    quantity = Column(String(50))
    sum_usd = Column(String(50))
    sum_rub = Column(String(50))
    sum_try = Column(String(50))
    sum_kzt = Column(String(50))
    currency = Column(String(10))
    currencyPrice = Column(String(50))
    client_name = Column(String(100))
    client_phone = Column(String(20))
    client_mail = Column(String(100))
    status = Column(Enum(OrderStatus, native_enum=False), default=OrderStatus.sale)
