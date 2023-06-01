from loguru import logger
from sqlalchemy import *
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from core.database.model import *

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
Base = declarative_base()
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


async def get_client_info(**kwargs):
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == str(kwargs["chat_id"])))
        client = q.scalars().first()
        if client is None:
            return False
        return client


async def save_phone(chat_id: str, phone: str):
    async with async_session() as session:
        q = await session.execute(select(Clients).filter(Clients.chat_id == chat_id))
        client = q.scalars().first()
        if client.phones is None:
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
        return client.phones.split(',')
