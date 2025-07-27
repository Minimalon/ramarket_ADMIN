import asyncio

import sqlalchemy
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from core.database.model import *

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
Base = sqlalchemy.orm.declarative_base()
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def update_client_info(**kwargs):
    async with async_session() as session:
        for key, value in kwargs.items():
            kwargs[key] = str(value)
        logger.info(kwargs)
        chat_id = str(kwargs["chat_id"])
        q = await session.execute(select(Clients).filter(Clients.chat_id == chat_id))
        SN = q.scalars().first()
        if SN is None:
            SN = Clients(**kwargs)
            session.add(SN)
        else:
            await session.execute(update(Clients).where(Clients.chat_id == str(kwargs["chat_id"])).values(kwargs))
        await session.commit()


async def get_client_info(chat_id) -> Clients:
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == str(chat_id)))
        client = q.scalars().first()
        if client is None:
            return False
        return client

async def get_client_info_by_phone(phone: str) -> Clients:
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.phone_number == phone))
        client = q.scalars().first()
        if client is None:
            return False
        return client


async def get_admins(chat_id=None):
    async with async_session() as session:
        if chat_id is None:
            q = await session.execute(select(Clients).filter(Clients.admin))
            return q.scalars().all()
        else:
            q = await session.execute(select(Clients.admin).filter(Clients.chat_id == str(chat_id)))
            return q.scalars().first()


async def get_all_clients():
    async with async_session() as session:
        q = await session.execute(select(Clients))
        return q.scalars().all()


async def save_phone(chat_id: str, phone: str):
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == chat_id))
        client = q.scalars().first()
        if client.phones is None or not client.phones:
            await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(phones=phone))
        else:
            phones = client.phones.split(',')
            if phone not in phones:
                phones = f'{phone},{client.phones}'
                await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(phones=phones))
        await session.commit()


async def get_saved_phones(chat_id: str):
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == chat_id))
        client = q.scalars().first()
        if client.phones is None:
            return False
        elif not client.phones:
            return False
        return client.phones.split(',')


async def delete_saved_phones(chat_id: str, phones_to_delete: list):
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == chat_id))
        client = q.scalars().first()
        if client.phones is None or not client.phones:
            return False
        phones_to_save = []
        saved_phones = client.phones.split(',')

        for save_phone in saved_phones:
            if save_phone not in phones_to_delete:
                phones_to_save.append(save_phone)
        if len(saved_phones) - len(phones_to_delete) == 0:  # Если удаляют все телефоны
            await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(phones=None))
        elif len(phones_to_save) > 1:  # Если на сохранение остаётся больше 1 телефона
            await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(phones=','.join(phones_to_save)))
        elif len(phones_to_save) == 1:  # Если сохраняется 1 телефон
            await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(phones=phones_to_save[0]))
        else:
            await session.execute(update(Clients).where(Clients.chat_id == chat_id).values(phones=None))
        await session.commit()


if __name__ == '__main__':
    a = asyncio.run(get_admins())
    for b in a:
        print(b.first_name)
