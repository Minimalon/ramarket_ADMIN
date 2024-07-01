import aiogram.exceptions
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
            command='add_contact',
            description='Добавить контакт'
        ),
        BotCommand(
            command='contacts',
            description='Сохранённые контакты'
        ),
        BotCommand(
            command='delete_contacts',
            description='Удалить сохраненные контакты'
        ),
        BotCommand(
            command='delete_order',
            description='Удалить заказ'
        ),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def get_commands_admins(bot: Bot, admins):
    commands = [
        BotCommand(
            command='start',
            description='Главное меню'
        ),
        BotCommand(
            command='all_users',
            description='Все пользователи 1C'
        ),
        BotCommand(
            command='delete_users',
            description='Удалить пользователей 1C'
        ),
        BotCommand(
            command='total_orders',
            description='История всех продаж'
        ),
        BotCommand(
            command='add_contact',
            description='Добавить контакт'
        ),
        BotCommand(
            command='contacts',
            description='Сохранённые контакты'
        ),
        BotCommand(
            command='delete_contacts',
            description='Удалить сохранённые контакты'
        ),
        BotCommand(
            command='delete_order',
            description='Удалить заказ'
        ),
        BotCommand(
            command='help',
            description='Видео урок'
        ),
    ]
    for admin in admins:
        try:
            await bot.set_my_commands(commands, BotCommandScopeChat(chat_id=admin.chat_id))
        except aiogram.exceptions.TelegramBadRequest:
            continue
