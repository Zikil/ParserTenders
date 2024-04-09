# - *- coding: utf- 8 - *-
import os

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message, CallbackQuery

from aiogram.utils.media_group import MediaGroupBuilder
from tgbot.database.db_users import UserModel, Userx
from tgbot.keyboards.reply_main import menu_frep
from tgbot.utils.const_functions import ded
from tgbot.utils.misc.bot_models import FSM, ARS
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.services.parser_tendors import get_tenders_from_url, get_excel_from_tenders, get_articles
from tgbot.data.config import BOT_SCHEDULER, PATH_EXCEL, PATH_LOGS
from tgbot.utils.const_functions import get_date

router = Router(name=__name__)


# Открытие главного меню
@router.message(F.text.in_(()))
@router.message(Command(commands=['start']))
async def main_start(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()
    
    bot_logger.warning(f"command start from {User.user_name}")
    await message.answer(
        ded(f"""
            Привет, {User.user_name}
            Это бот для поиска тендеров на сайте Tender.pro
            Введите /parser для поиска прямо сейчас (ищет долго, минут 10)
            Или /get_notif для получения уведомления в 8 и 18 часов
            Команда /status показывает статус бота
            Поиск за все время выведет таблицу в которой будут тендеры за все время, не важно какой статус
            Чтобы обновить таблицу по которой искать просто пришлите ее мне
        """),
        reply_markup=menu_frep(message.from_user.id),
    )


# parser
@router.message(F.text.in_(('parser', 'Начать поиск сейчас')))
@router.message(Command(commands=['parser']))
async def parser(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    try:
        bot_logger.warning(f"command parser from {User.user_name}")
        await message.answer("Идет поиск тендеров")
        tenders_id = await get_tenders_from_url()
        bot_logger.warning(f"tenders_id: {tenders_id}")
        answ = ""
        for num, tend in enumerate(tenders_id):
            answ += f"{num+1}. Наименование/артикул: {tend['article']}, id тендера: {tend['id_tender']}, url: {tend['url_tender']} \n \n"
        mes = f"Ответ на запрос поиска тендеров: \n \n"
        if answ == "":
            mes += "Ничего не найдено"
        else:
            mes += answ
        await message.answer(f"{mes}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# status 
@router.message(F.text.in_(('status', 'Статус бота')))
@router.message(Command(commands=['status']))
async def status(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    bot_logger.warning(f"command status from {User.user_name}")
    jobs = BOT_SCHEDULER.get_jobs()
    bot_logger.warning(f"jobs: {jobs[0]}, {jobs[1]}")
    await message.answer(f"jobs: \n{jobs[0]}, \n{jobs[1]}")

# start notification
@router.message(F.text.in_(('Получать уведомления', 'get_notif')))
@router.message(Command(commands=['get_notif']))
async def get_notif(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    bot_logger.warning(f"command get_notif from {User.user_name}")
    
    if User.notif == "False":
        Userx.update(User.user_id, notif = "True")
        await message.answer("Теперь вы будете получать уведомления")

    else:
        await message.answer("Вы уже получаете уведомления")

# stop notification
@router.message(F.text.in_(('Не получать уведомления', 'stop_get_notif')))
@router.message(Command(commands=['stop_get_notif']))
async def stop_get_notif(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    bot_logger.warning(f"command stop_get_notif from {User.user_name}")
    
    if User.notif == "True":
        Userx.update(User.user_id, notif = "False")
        await message.answer("Теперь вы не будете получать уведомления")

    else:
        await message.answer("Вы и так не получаете уведомления")


# Загрузка таблицы в бот
@router.message(F.content_type.in_({'document', 'file'}))
async def upload_excel(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    if (message.document.file_name.find('.xls') != -1):
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        link_temp = "tgbot/data/articles_sheet_temp.xlsx"
        await bot.download_file(file_path, link_temp)
        try:
            arts = get_articles(link=link_temp)
            bot_logger.warning(f"command upload_excel from {User.user_name}. файл: {message.document.file_name}, загружен")
            await message.answer("Таблица загружена")
        except Exception as e:
            bot_logger.warning(f"command upload_excel from {User.user_name}. файл: {message.document.file_name}, не загружен. Ошибка {e}")
            await message.answer(f"Ошибка {e} \nФайл не был загружен")
        await bot.download_file(file_path, "tgbot/data/articles_sheet.xlsx")
    else:
        bot_logger.warning(f"command upload_excel from {User.user_name}. файл: {message.document.file_name}, не загружен")
        await message.answer("Файл должен быть с расширением .xls или .xlsx")


# Выгрузка таблицы
@router.message(F.text.in_(('Показать таблицу', 'get_articles')))
@router.message(Command(commands=['get_sheet', 'article']))
async def get_sheet(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()
    await message.answer_document(
        FSInputFile(PATH_EXCEL),
        # caption=f"<b>📦 #BACKUP | <code>{get_date()}</code></b>",
        caption=f"Таблица, которую вы загрузили и по которой выполняется поиск",
    )

# Поиск тендеров за все время
@router.message(F.text.in_(('Поиск за все время', 'excel_from_tenders')))
@router.message(Command(commands=['excel_from_tenders', 'tenders']))
async def excel_from_tenders(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()
    tenders_id = await get_tenders_from_url(tender_state=100)
    get_excel_from_tenders(tenders_id=tenders_id)
    
    await message.answer_document(
        FSInputFile('tgbot/data/tenders_id_all.xlsx'),
        # caption=f"<b>📦 #BACKUP | <code>{get_date()}</code></b>",
        caption=f"Тендеры за все время.",
    )


# Получение логов
@router.message(Command(commands=['log', 'logs']))
async def admin_log(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()

    media_group = MediaGroupBuilder(
        caption=f"<b>🖨 #LOGS | <code>{get_date(full=False)}</code></b>",
    )

    if os.path.isfile(PATH_LOGS):
        media_group.add_document(media=FSInputFile(PATH_LOGS))

    if os.path.isfile("tgbot/data/sv_log_err.log"):
        media_group.add_document(media=FSInputFile("tgbot/data/sv_log_err.log"))

    if os.path.isfile("tgbot/data/sv_log_out.log"):
        media_group.add_document(media=FSInputFile("tgbot/data/sv_log_out.log"))

    await message.answer_media_group(media=media_group.build())


