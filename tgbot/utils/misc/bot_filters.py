# - *- coding: utf- 8 - *-
from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.data.config import get_admins
from tgbot.database.db_users import Userx
from tgbot.utils.misc.bot_logging import bot_logger


# Проверка на админа
class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in get_admins():
            return True
        else:
            return False

# Отправка сообщения пользователям по тендорам
def get_employees():
    get_users = Userx.gets(notif = "True")
    # bot_logger.warning(f"employee {get_users}")
    return get_users