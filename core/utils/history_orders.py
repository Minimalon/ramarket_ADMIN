from pathlib import Path

import pandas as pd

from core.database.ramarket_shop.db_shop import get_documents_by_agent_id
import config
from core.database.ramarket_shop.model import Documents
from typing import Generator


async def data_for_df(documents: list[Documents]) -> list[dict]:
    data = []
    for doc in documents:
        for item in doc:
            data.append({
                'Дата': doc.date,
                'Номер заказа': doc.order_id,
                'Статус': doc.status,
                'Резидент': doc.rezident,
                'Имя агента': doc.agent_name,
                'Страна': doc.country_name,
                'Город': doc.city_name,
                'Название магазина': doc.shop_name,
                'Валюта магазина': doc.shop_currency,
                'Коммисия': doc.tax,
                'Название продукта': item.product_name,
                'Тип оплаты': doc.payment_name,
                'Товар': item.product_name,
                'Цена': item.price,
                'Количество': item.quantity,
                'Сумма USD': doc.sum_usd,
                'Сумма RUB': doc.sum_rub,
                'Сумма TRY': doc.sum_try,
                'Сумма KZT': doc.sum_kzt,
                'Валюта': doc.currency,
                'Цена валюты': doc.currency_price,
                'Клиент': doc.client_name,
                'Телефон': doc.client_phone,
                'Email': doc.client_mail
            })
    return data


async def correct_df(df: pd.DataFrame) -> pd.DataFrame:
    df['Дата'] = df['Дата'].dt.tz_localize(None)
    df[['Сумма USD', 'Сумма RUB', 'Сумма TRY', 'Сумма KZT', 'Цена', 'Цена валюты']] = df[
        ['Сумма USD', 'Сумма RUB', 'Сумма TRY', 'Сумма KZT', 'Цена', 'Цена валюты']].astype(float)
    df[['Количество']] = df[['Количество']].astype(int)
    sum_kzt = ((df['Цена'] * df['Количество']) * df['Цена валюты'])
    tax = df['Коммисия'].fillna(0)
    df['Сумма KZT'] = round(sum_kzt * (1 if tax.empty else tax / 100 + 1), 0)
    return df


async def create_excel_by_agent_id(agent_id: str, file_name: str, start_date=None, end_date=None):
    orders = await get_documents_by_agent_id(agent_id, start_date, end_date)
    if not orders:
        return False
    dir_path = Path(config.dir_path, 'files', 'historyOrders')
    dir_path.mkdir(parents=True, exist_ok=True)
    path_file = dir_path / f"{file_name}.xlsx"
    df = pd.DataFrame(await data_for_df(orders))
    df = await correct_df(df)
    writer = pd.ExcelWriter(path_file, engine="xlsxwriter")
    df.to_excel(writer, sheet_name='orders', index=False, na_rep='NaN')
    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets['orders'].set_column(col_idx, col_idx, column_length + 3)
    writer.close()
    return path_file
