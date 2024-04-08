# - *- coding: utf- 8 - *-
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from tgbot.data.config import get_admins

# Команды для юзеров
user_commands = [
    BotCommand(command="start", description="Restart bot"),
    BotCommand(command="parser", description="Запускает поиск тендоров"),
    BotCommand(command="status", description="статус бота"),
    BotCommand(command="get_notif", description="получать уведомления"),
    BotCommand(command="stop_get", description="остановить получение уведомлений"),
    BotCommand(command="get_sheet", description="Получить таблицу"),
    # BotCommand(command="inline", description="🌀 Get Inline keyboard"),
]

# Команды для админов
admin_commands = [
    BotCommand(command="start", description="Restart bot"),
    BotCommand(command="parser", description="Запускает поиск тендоров"),
    BotCommand(command="status", description="статус бота"),
    BotCommand(command="get_notif", description="получать уведомления"),
    BotCommand(command="stop_get_notif", description="остановить получение уведомлений"),
    BotCommand(command="start_shed", description="Запуск работы по расписанию"),
    BotCommand(command="stop_shed", description="остановка работы по расписанию"),
    BotCommand(command="get_sheet", description="Получить таблицу"),
    # BotCommand(command="inline", description="🌀 Get Inline keyboard"),
    BotCommand(command="log", description="🖨 Get Logs"),
    BotCommand(command="db", description="📦 Get Database"),
]


# Установка команд
async def set_commands(bot: Bot):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    for admin in get_admins():
        try:
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin))
        except:
            pass
