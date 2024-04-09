# - *- coding: utf- 8 - *-
from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from tgbot.data.config import get_admins
from tgbot.utils.const_functions import rkb


# Кнопки главного меню
def menu_frep(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardBuilder()

    # BotCommand(command="start", description="♻️ Restart bot"),
    # BotCommand(command="parser", description="Запускает поиск тендоров"),
    # BotCommand(command="status", description="Статус бота"),
    # BotCommand(command="get_notif", description="Получать уведомления"),
    # BotCommand(command="stop_get", description="Остановить получение уведомлений"),
    # BotCommand(command="start_shed", description="Запуск работы по расписанию"),
    # BotCommand(command="stop_shed", description="Остановка работы по расписанию"),
    # # BotCommand(command="inline", description="🌀 Get Inline keyboard"),
    # BotCommand(command="log", description="🖨 Get Logs"),
    # BotCommand(command="db", description="📦 Get Database"),

    keyboard.row(
        rkb("Начать поиск сейчас"), rkb("Статус бота"),
    )

    keyboard.row(
        rkb("Получать уведомления"), rkb("Не получать уведомления"),
    )

    keyboard.row(
        rkb("Показать таблицу"), rkb("Поиск за все время"),
    )

    # if user_id in get_admins():
    #     keyboard.row(
    #         rkb("Admin Inline"), rkb("Admin Reply"),
    #     )

    return keyboard.as_markup(resize_keyboard=True)
