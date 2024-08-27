import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal

import pandas as pd
from sqlalchemy import select, create_engine, text, distinct, func, DateTime, cast, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import config
from core.database.ramarket_shop.model import HistoryOrders, OrderStatus

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
    df[['sum_usd', 'sum_rub', 'sum_try', 'sum_kzt', 'price']] = df[
        ['sum_usd', 'sum_rub', 'sum_try', 'sum_kzt', 'price']].astype(float)
    df[['quantity']] = df[['quantity']].astype(int)
    sum_kzt = df['sum_kzt'].fillna(0)
    # sum_usd = df['sum_usd'].fillna(0)
    # sum_rub = df['sum_rub'].fillna(0)
    tax = df['tax'].fillna(0)
    df['sum_kzt'] = int(Decimal(round(sum_kzt * Decimal(1 if tax.empty else (tax / 100) + 1), 0)))
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


async def create_excel_by_agent_id(agent_id: str, file_name: str, start_date=None, end_date=None):
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders).filter(HistoryOrders.agent_id == agent_id))
        orders = q.scalars().first()
        dir_path = Path(config.dir_path, 'files', 'historyOrders')
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        path_file = dir_path / f"{file_name}.xlsx"
        if orders is None:
            return False
        if start_date and end_date:
            query = text(
                f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE agent_id = \'{agent_id}\' '
                f'AND date >= \'{start_date}\' AND date < \'{end_date}\' '
                f'order by date DESC')
        else:
            query = text(
                f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE agent_id = \'{agent_id}\' order by date DESC')
        engine = create_engine(
            f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
        df = pd.read_sql(query, engine.connect())
        if df.empty:
            return False
        df = await correct_df(df)
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')

        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)
        writer.close()
        return path_file


async def create_excel_by_shop(shop_id: str, file_name: str, start_date=None, end_date=None):
    """
    История продаж магазина, если нету дат, то отдаёт историю продаж за всё время
    :param shop_id: ID магазина
    :param shop_name: Имя магазина
    :param start_date: С какого числа историю продаж
    :param end_date: По какое число
    :return: путь к эксель файлу
    """
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders).filter(HistoryOrders.shop_id == shop_id))
        orders = q.scalars().first()
        if not os.path.exists(os.path.join(config.dir_path, 'files', 'historyOrders')):
            os.makedirs(os.path.join(config.dir_path, 'files', 'historyOrders'))
        path_file = os.path.join(config.dir_path, 'files', 'historyOrders', f"{file_name}.xlsx")
        if orders is None:
            return False
        if start_date and end_date:
            query = text(
                f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE shop_id = \'{shop_id}\' '
                f'AND date >= \'{start_date}\' AND date < \'{end_date}\' '
                f'order by date DESC')
        else:
            query = text(
                f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE shop_id = \'{shop_id}\' order by date DESC')
        engine = create_engine(
            f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
        df = pd.read_sql(query, engine.connect())
        if df.empty:
            return False
        df = await correct_df(df)
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)
        writer.close()
        return path_file


async def create_excel_by_shops(shop_id: list, file_name: str, start_date=None, end_date=None):
    """
    История продаж магазина, если нету дат, то отдаёт историю продаж за всё время
    :param shop_id: ID магазина
    :param shop_name: Имя магазина
    :param start_date: С какого числа историю продаж
    :param end_date: По какое число
    :return: путь к эксель файлу
    """
    if not os.path.exists(os.path.join(config.dir_path, 'files', 'historyOrders')):
        os.makedirs(os.path.join(config.dir_path, 'files', 'historyOrders'))
    path_file = os.path.join(config.dir_path, 'files', 'historyOrders', f"{file_name}.xlsx")
    if start_date and end_date:
        query = text(
            f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE shop_id IN {tuple(shop_id)}'
            f'AND date >= \'{start_date}\' AND date < \'{end_date}\' '
            f'order by date DESC')
    else:
        query = text(
            f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE shop_id IN {tuple(shop_id)} order by date DESC')
    engine = create_engine(
        f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
    df = pd.read_sql(query, engine.connect())
    if df.empty:
        return False
    df = await correct_df(df)
    writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
    df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')
    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)
    writer.close()
    return path_file


if __name__ == '__main__':
    a = asyncio.run(get_counts_shop_sales('5502601', '2023-05-23', '2023-07-01'))
    print(a)
