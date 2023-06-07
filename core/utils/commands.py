from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault


async def get_commands(bot: Bot):
    commands = [
        BotCommand(
            command='start',
            description='Главное меню'
        ),
        BotCommand(
            command='help',
            description='Видео урок'
        ),
        BotCommand(
            command='contacts',
            description='Сохранённые контакты'
        ),
        BotCommand(
            command='add_contact',
            description='Добавить контакт'
        ),
        BotCommand(
            command='delete_contacts',
            description='Удалить контакты'
        ),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())
