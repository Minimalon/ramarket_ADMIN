from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat


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
            description='Удалить сохраненные контакты'
        ),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def get_commands_admins(bot: Bot, chat_ids: list):
    commands = [
        BotCommand(
            command='start',
            description='Главное меню'
        ),
        BotCommand(
            command='all_users',
            description='Все пользователи'
        ),
        # BotCommand(
        #     command='delete_users',
        #     description='Удалить пользователей'
        # ),
        BotCommand(
            command='contacts',
            description='Сохранённые сохраненные контакты'
        ),
        BotCommand(
            command='add_contact',
            description='Добавить контакт'
        ),
        BotCommand(
            command='delete_contacts',
            description='Удалить сохранённые контакты'
        ),
        BotCommand(
            command='help',
            description='Видео урок'
        ),
    ]
    for chat_id in chat_ids:
        await bot.set_my_commands(commands, BotCommandScopeChat(chat_id=chat_id))
