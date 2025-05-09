import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal

import pandas as pd
from sqlalchemy import select, create_engine, text, distinct, func, DateTime, cast, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, joinedload

import config
from core.database.ramarket_shop.model import HistoryOrders, OrderStatus, Documents

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
Base = declarative_base()
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def correct_df(df):
    df['date'] = df['date'].dt.tz_localize(None)
    df = df.drop(columns=[
        'chat_id',
        'id',
        'agent_id',
        'shop_id',
        'paymentGateway',
        'product_id',
        'paymentType',
        'country_code',
        'city_code',
    ])
    column_order = [
        'date',
        'order_id',
        'status',
        'rezident',
        'agent_name',
        'country_name',
        'city_name',
        'shop_name',
        'shop_currency',
        'payment_name',
        'product_name',
        'price',
        'quantity',
        'sum_usd',
        'sum_rub',
        'sum_try',
        'sum_kzt',
        'tax',
        'currency',
        'currencyPrice',
        'client_name',
        'client_phone',
        'client_mail',
    ]
    df = df[column_order]
    df[['sum_usd', 'sum_rub', 'sum_try', 'sum_kzt', 'price', 'currencyPrice']] = df[
        ['sum_usd', 'sum_rub', 'sum_try', 'sum_kzt', 'price', 'currencyPrice']].astype(float)
    df[['quantity']] = df[['quantity']].astype(int)
    sum_kzt = ((df['price'] * df['quantity']) * df['currencyPrice'])
    # sum_usd = df['sum_usd'].fillna(0)
    # sum_rub = df['sum_rub'].fillna(0)
    tax = df['tax'].fillna(0)

    df['sum_kzt'] = round(sum_kzt * (1 if tax.empty else tax / 100 + 1), 0)
    # df['sum_usd'] = round(sum_usd * (1 if tax.empty else (tax / 100) + 1), 0)
    # df['sum_rub'] = round(sum_rub * (1 if tax.empty else (tax / 100) + 1), 0)
    return df


async def get_orders_by_shop_id(shop_id: str) -> list[HistoryOrders]:
    async with async_session() as session:
        query = select(HistoryOrders).filter(HistoryOrders.shop_id == shop_id)
        result = await session.execute(query)
        return result.scalars().all()


async def get_orders_by_order_id(order_id: str) -> list[HistoryOrders] | None:
    async with async_session() as session:
        query = select(HistoryOrders).filter(HistoryOrders.order_id == order_id,
                                             HistoryOrders.status.not_in(
                                                 [OrderStatus.prepare_delete, OrderStatus.delete]))
        result = await session.execute(query)
        return result.scalars().all()


async def delete_orders_by_order_id(order_id: str) -> None:
    async with async_session() as session:
        query = update(HistoryOrders).where(HistoryOrders.order_id == order_id).values(
            status=OrderStatus.prepare_delete
        )
        await session.execute(query)
        await session.commit()


async def prepare_delete_history_order(order_id: str, order_date: datetime):
    async with async_session() as session:
        await session.execute(
            update(HistoryOrders).
            where(
                (HistoryOrders.order_id == order_id) &
                (func.to_char(HistoryOrders.date, 'YYYYMMDDHH24MI') == order_date.strftime('%Y%m%d%H%M'))
            ).
            values(
                status=OrderStatus.prepare_delete,
            ))
        await session.commit()


async def delete_document(order_id: str, order_date: datetime) -> None:
    async with async_session() as session:
        await session.execute(
            update(Documents).
            where(
                (Documents.order_id == order_id) &
                (func.to_char(Documents.date, 'YYYYMMDDHH24MI') == order_date.strftime('%Y%m%d%H%M'))
            ).
            values(
                status=OrderStatus.delete,
            ))
        await session.commit()


async def get_orders_by_order_id_and_date(order_id: str, date: datetime) -> list[HistoryOrders] | None:
    async with async_session() as session:
        query = select(HistoryOrders).filter(HistoryOrders.order_id == order_id)
        result = await session.execute(query)
        return result.scalars().all()


async def get_orders_by_order_id_and_shop_id(order_id: str, shop_id: str) -> list[HistoryOrders] | None:
    async with async_session() as session:
        query = select(HistoryOrders).filter(HistoryOrders.order_id == order_id,
                                             HistoryOrders.shop_id == shop_id)
        result = await session.execute(query)
        return result.scalars().all()


async def update_date_order(order_id: str, old_date: datetime, new_date: datetime) -> None:
    async with async_session() as session:
        await session.execute(
            update(HistoryOrders).
            where(
                (HistoryOrders.order_id == order_id) &
                (func.to_char(HistoryOrders.date, 'YYYYMMDDHH24MI') == old_date.strftime('%Y%m%d%H%M'))
            ).
            values(
                date=new_date,
                status=OrderStatus.change_date
            ))
        await session.commit()


async def update_date_document(order_id: str, old_date: datetime, new_date: datetime) -> None:
    async with async_session() as session:
        await session.execute(
            update(Documents).
            where(
                (Documents.order_id == order_id) &
                (func.to_char(Documents.date, 'YYYYMMDDHH24MI') == old_date.strftime('%Y%m%d%H%M'))
            ).
            values(
                date=new_date,
                status=OrderStatus.change_date
            ))
        await session.commit()


async def get_counts_shop_sales(shop_id: str, start_date: str, end_date: str):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    async with async_session() as session:
        query = (
            select(func.count(HistoryOrders.shop_id))
            .filter(HistoryOrders.shop_id == shop_id)
            .filter(HistoryOrders.date >= cast(start_date, DateTime))
            .filter(HistoryOrders.date < cast(end_date, DateTime))
            .group_by(HistoryOrders.shop_id)
        )
        result = await session.execute(query)
        return result.scalars().first()


async def get_orders_by_1c_id(id: str, days):
    async with async_session() as session:
        if days is not None:
            start_date = datetime.now() - timedelta(days=days)
            end_date = datetime.now() + timedelta(days=1)
            query = (
                select(distinct(HistoryOrders.order_id))
                .filter(HistoryOrders.agent_id == id)
                .filter(HistoryOrders.date >= cast(start_date, DateTime))
                .filter(HistoryOrders.date < cast(end_date, DateTime))
                .group_by(HistoryOrders.order_id)
            )
            q = await session.execute(query)
        else:
            q = await session.execute(select(distinct(HistoryOrders.order_id)).where(HistoryOrders.agent_id == id))
        return q.scalars().all()

async def get_documents_by_agent_id(agent_id: str, start_date: str = None, end_date: str = None) -> list[Documents]:
    async with async_session() as session:
        if start_date and end_date:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.agent_id == agent_id).where(
                Documents.date >= start_date, Documents.date < end_date)
        else:
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.agent_id == agent_id)
        result = await session.execute(query)
        return result.scalars().unique().all()

async def get_uniq_shop_ids() -> list[str]:
    async with async_session() as session:
        q = await session.execute(select(distinct(HistoryOrders.shop_id)))
        return q.scalars().all()

async def get_documents_by_shop_id(
        shop_id: str, start_date: str = None, end_date: str = None
) -> list[Documents]:
    async with async_session() as session:
        if start_date and end_date:
            start_date_parsed = datetime.fromisoformat(start_date)
            end_date_parsed = datetime.fromisoformat(end_date)

            query = (
                select(Documents)
                .options(joinedload(Documents.items))
                .where(Documents.shop_id == shop_id)
                .where(
                    Documents.date >= start_date_parsed,
                    Documents.date < end_date_parsed,
                )
            )
        else:
            query = (
                select(Documents)
                .options(joinedload(Documents.items))
                .where(Documents.shop_id == shop_id)
            )
        result = await session.execute(query)
        return result.scalars().unique().all()
async def get_documents_by_shops(shops: list[str], start_date: str = None, end_date: str = None) -> list[Documents]:
    async with async_session() as session:
        if start_date and end_date:
            start_date = datetime.fromisoformat(start_date)
            end_date = datetime.fromisoformat(end_date)
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.shop_id.in_(shops)).where(
                Documents.date >= start_date, Documents.date < end_date)
        else:
            query = select(Documents).options(joinedload(Documents.items)).where(Documents.shop_id.in_(shops))
        result = await session.execute(query)
        return result.scalars().unique().all()


if __name__ == '__main__':
    # a = asyncio.run(get_counts_shop_sales('5502601', '2023-05-23', '2023-07-01'))
    a = asyncio.run(get_uniq_shop_ids())
    print(a)
