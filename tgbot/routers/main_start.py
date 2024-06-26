# - *- coding: utf- 8 - *-
import os
import io
import pandas as pd

from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message, CallbackQuery, BufferedInputFile

from aiogram.utils.media_group import MediaGroupBuilder
from tgbot.database.db_users import UserModel, Userx
from tgbot.keyboards.reply_main import menu_frep
from tgbot.utils.const_functions import ded
from tgbot.utils.misc.bot_models import FSM, ARS
from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.services.parser_tendors import get_tenders_from_url, get_excel_from_tenders, get_articles
from tgbot.services.tender_plan import tenders_with_goods, search_in_tenderplan
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
@router.message(F.text.in_(('parser', 'Начать поиск сейчас', 'Поиск в tenderpro')))
@router.message(Command(commands=['parser']))
async def parser(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    try:
        bot_logger.warning(f"command parser from {User.user_name}")
        await message.answer("Идет поиск тендеров")
        tenders_id = await get_tenders_from_url()
        bot_logger.warning(f"tenders_id: {tenders_id}")
        if (len(str(tenders_id))>4000):
            tenders_id = pd.DataFrame(tenders_id)
            get_excel_from_tenders(tenders_id)
            with io.BytesIO() as output:
                tenders_id.to_excel(output) 
                excel_data = output.getvalue()
            file_excel = io.BytesIO(excel_data)
            await message.answer_document(BufferedInputFile(file_excel.getvalue(), f"{message.text}.xlsx"), caption = f"Нашлось по запросу '{message.text}'")
        else:
            answ = ""
            for num, tend in enumerate(tenders_id):
                answ += f"{num+1}. Наименование/артикул: {tend['article']}, id тендера: {tend['id_tender']}, прием до: {tend['date_until']}, url: {tend['url_tender']} \n \n"
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
    bot_logger.warning(f"jobs: {jobs}")
    await message.answer(f"jobs: \n{[str(j) for j in jobs]}")

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
        if message.document.file_name.find('articles_sheet') != -1:
            link_temp = "tgbot/data/articles_sheet_temp.xlsx"
            await bot.download_file(file_path, link_temp)
            try:
                arts = get_articles(link=link_temp)
                bot_logger.warning(f"command upload_excel from {User.user_name}. файл: {message.document.file_name}, загружен")
                await bot.download_file(file_path, "tgbot/data/articles_sheet.xlsx")
                await message.answer("Таблица загружена")
            except Exception as e:
                bot_logger.warning(f"command upload_excel from {User.user_name}. файл: {message.document.file_name}, не загружен. Ошибка {e}")
                await message.answer(f"Ошибка {e} \nФайл не был загружен")
        else:
            await bot.download_file(file_path, f"tgbot/data/price_{message.document.file_name}")
            await message.answer(f"Таблица {message.document.file_name} загружена")
        
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


# Поиск тендеров в автопитере
@router.message(F.text.in_(('Поиск в автопитере', 'tenders_with_goods')))
@router.message(Command(commands=['tenders_with_goods', 'search_ap']))
async def search_in_ap(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()
    bot_logger.warning(f"command search_in_ap from {User.user_name}")
    await message.answer("Идет поиск тендеров")
    tenders_with_goods(1)
    await message.answer_document(
        FSInputFile('tgbot/data/tenders_with_goods.xlsx'),
        caption=f"Тендеры в автопитере.",
    )


# таблица тендеров в автопитере
@router.message(F.text.in_(('Показать автопитер', 'excel_ap')))
@router.message(Command(commands=['excel_from_ap', 'show_ap']))
async def excel_from_ap(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()
    bot_logger.warning(f"command excel_from_ap from {User.user_name}")
    await message.answer_document(
        FSInputFile('tgbot/data/tenders_with_goods.xlsx'),
        caption=f"Тендеры в автопитере.",
    )


# Поиск тендеров в tenderplan
@router.message(F.text.in_(('Поиск в tenderplan', 'tenders_in_tenderplan')))
@router.message(Command(commands=['tenders_in_tenderplan', 'search_in_tenderplan', 'tenderplan']))
async def search_in_tenderplan1(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()
    bot_logger.warning(f"command search_in_tenderplan from {User.user_name}")
    await message.answer("Идет поиск тендеров")
    await search_in_tenderplan()
    await message.answer_document(
        FSInputFile('tgbot/data/tenders_tenderplan_from_art.xlsx'),
        caption=f"Тендеры в tenderplan.",
    )


# таблица тендеров в tenderplan
@router.message(F.text.in_(('Показать tenderplan', 'excel_tenderplan')))
@router.message(Command(commands=['excel_from_tenderplan', 'show_tenderplan']))
async def excel_from_tenderplan(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await state.clear()
    bot_logger.warning(f"command excel_from_tenderplan from {User.user_name}")
    await message.answer_document(
        FSInputFile('tgbot/data/tenders_tenderplan_from_art.xlsx'),
        caption=f"Тендеры в tenderplan.",
    )