# - *- coding: utf- 8 - *-
import io
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
import aiogram
import pandas as pd
from tgbot.database.db_users import UserModel
from tgbot.utils.const_functions import del_message
from tgbot.utils.misc.bot_models import FSM, ARS

from tgbot.services.parser_tendors import get_tenders_from_article, get_excel_from_tenders

router = Router(name=__name__)


# Колбэк с удалением сообщения
@router.callback_query(F.data == 'close_this')
async def main_callback_close(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await del_message(call.message)


# Колбэк с обработкой кнопки
@router.callback_query(F.data == '...')
async def main_callback_answer(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await call.answer(cache_time=30)


# Колбэк с обработкой удаления сообщений потерявших стейт
@router.callback_query()
async def main_callback_missed(call: CallbackQuery, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    await call.answer(f"❗️ Miss callback: {call.data}", True)


# Обработка всех неизвестных команд
@router.message()
async def main_message_missed(message: Message, bot: Bot, state: FSM, arSession: ARS, User: UserModel):
    try:
        tenders = await get_tenders_from_article(message.text)
        if (len(str(tenders))>2000):
            tenders = pd.DataFrame(tenders)
            get_excel_from_tenders(tenders)
            with io.BytesIO() as output:
                tenders.to_excel(output) 
                excel_data = output.getvalue()
            file_excel = io.BytesIO(excel_data)
            await message.answer_document(BufferedInputFile(file_excel.getvalue(), f"{message.text}.xlsx"), caption = f"Нашлось по запросу '{message.text}'")
        else:
            answ = ""
            for num, tend in enumerate(tenders):
                answ += f"{num+1}. Наименование/артикул: {tend['article']}, id тендера: {tend['id_tender']}, прием до: {tend['date_until']}, url: {tend['url_tender']} \n"
            mes = f"Нашлось по запросу {message.text}: \n"
            if answ == "":
                mes += "Ничего не найдено"
            else:
                mes += answ
            await message.answer(f"{mes}")
    # except aiogram.exceptions.TelegramBadRequest:
    #     await message.answer(f"Ошибка: wg mes too long, {len(str(tenders))}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

