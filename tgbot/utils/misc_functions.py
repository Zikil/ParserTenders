# - *- coding: utf- 8 - *-
from aiogram import Bot
from aiogram.types import FSInputFile

from tgbot.data.config import get_admins, PATH_DATABASE, start_status
from tgbot.utils.const_functions import get_date, send_admins
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.services.parser_tendors import get_tenders_from_url
from tgbot.utils.misc.bot_filters import get_employees


# Отправка сообщения пользователям по тендорам
# async def get_employees(bot: Bot, text: str, markup=None, not_me=0):
#     get_users = Userx.gets(notif = "False")
#     bot_logger.warning("employee {get_users}")

# Отправка сообщения пользователям по тендорам
async def send_employees(bot: Bot, text: str, markup=None, not_me=0):
    get_empl = get_employees()
    bot_logger.warning(f"employee1 {get_empl}")
    for empl in get_empl:
        await bot.send_message(
                        empl.user_id,
                        text,
                        reply_markup=markup,
                        # disable_web_page_preview=True,
                    )
    
    # for admin in get_admins():
    #     try:
    #         if str(admin) != str(not_me):
    #             await bot.send_message(
    #                 admin,
    #                 text,
    #                 reply_markup=markup,
    #                 disable_web_page_preview=True,
    #             )
    #     except:
    #         ...


# Выполнение функции после запуска бота (рассылка админам о запуске бота)
async def startup_notify(bot: Bot):
    if len(get_admins()) >= 1 and start_status:
        await send_admins(bot, "<b>✅ Bot was started</b>")


# Автоматические бэкапы БД
async def autobackup_admin(bot: Bot):
    for admin in get_admins():
        try:
            await bot.send_document(
                admin,
                FSInputFile(PATH_DATABASE),
                caption=f"<b>📦 #AUTOBACKUP | <code>{get_date()}</code></b>",
            )
        except:
            pass


# поиск тендора по расписанию
async def tenders_sched(bot: Bot):
    try:
        tenders_id = await get_tenders_from_url()
        bot_logger.warning(f"tenders_id: {tenders_id}")
        answ = ""
        for num, tend in enumerate(tenders_id):
            answ += f"{num+1}. Наименование/артикул: {tend['article']}, id тендера: {tend['id_tender']}, url: {tend['url_tender']} \n \n"
        mes = f"Автоматический поиск тендоров: \n \n"
        if answ == "":
            mes += "Ничего не найдено"
        else:
            mes += answ
            await send_employees(bot, answ)
    except:
        send_admins(bot, f"Ошибка при автоматическом поиске")
