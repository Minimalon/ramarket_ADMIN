from sqlalchemy import String, Column, DateTime, Boolean
import config
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base

engine = create_async_engine(
    f"postgresql+asyncpg://{config.db_user}:{config.db_password}@{config.ip}:{config.port}/{config.database}")
Base = declarative_base()


class Clients(Base):
    __tablename__ = 'clients'
    date = Column(DateTime(timezone=True), server_default=func.now())
    phone_number = Column(String(50), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    user_id = Column(String(50), nullable=False, primary_key=True)
    chat_id = Column(String(50), nullable=False)
    language = Column(String(3), nullable=False, default='ru')
    phones = Column(String(500), nullable=False)
    admin = Column(Boolean, default=False)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)