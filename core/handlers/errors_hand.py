from aiogram.types import ErrorEvent
from loguru import logger

from core.utils import texts


async def tg_duble_error(event: ErrorEvent):
    await event.update.callback_query.answer('Вы дважды нажали на кнопку')
    return


async def error_total(event: ErrorEvent):
    logger.exception(event.exception)
    if event.update.message is not None:
        await event.update.message.answer(texts.error_head + str(event.exception))
    else:
        await event.update.callback_query.message.answer(texts.error_head + str(event.exception))
