import os

import pandas as pd
from sqlalchemy import select, create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import config
from core.database.ramarket_shop.model import HistoryOrders

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
Base = declarative_base()
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def create_excel_by_agent_id(agent_id: str, agent_name: str):
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders).filter(HistoryOrders.agent_id == agent_id))
        orders = q.scalars().first()
        if not os.path.exists(os.path.join(config.dir_path, 'files', 'historyOrders')):
            os.makedirs(os.path.join(config.dir_path, 'files', 'historyOrders'))
        path_file = os.path.join(config.dir_path, 'files', 'historyOrders', f"{'_'.join(agent_name.split())}.xlsx")
        if orders is None:
            return False
        query = text(f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE agent_id = \'{agent_id}\' order by date DESC')
        engine = create_engine(f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
        df = pd.read_sql(query, engine.connect())
        df['date'] = df['date'].dt.tz_localize(None)
        df = df.drop(columns=['chat_id', 'id', 'agent_id', 'shop_id', 'paymentGateway', 'product_id', 'paymentType', 'country_code', 'city_code'])
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)
        writer.close()
        return path_file


async def create_excel_by_shop_id(shop_id: str, shop_name: str):
    async with async_session() as session:
        q = await session.execute(select(HistoryOrders).filter(HistoryOrders.shop_id == shop_id))
        orders = q.scalars().first()
        if not os.path.exists(os.path.join(config.dir_path, 'files', 'historyOrders')):
            os.makedirs(os.path.join(config.dir_path, 'files', 'historyOrders'))
        path_file = os.path.join(config.dir_path, 'files', 'historyOrders', f"{'_'.join(shop_name.split())}.xlsx")
        if orders is None:
            return False
        query = text(f'SELECT * FROM public."{HistoryOrders.__table__}" WHERE shop_id = \'{shop_id}\' order by date DESC')
        engine = create_engine(f"postgresql+psycopg2://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database_ramarket}")
        df = pd.read_sql(query, engine.connect())
        df['date'] = df['date'].dt.tz_localize(None)
        df = df.drop(columns=['chat_id', 'id', 'agent_id', 'shop_id', 'paymentGateway', 'product_id', 'paymentType', 'country_code', 'city_code'])
        writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
        df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)
        writer.close()
        return path_file
