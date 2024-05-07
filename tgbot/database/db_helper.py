# - *- coding: utf- 8 - *-
import sqlite3

from tgbot.data.config import PATH_DATABASE
from tgbot.utils.const_functions import ded


# Преобразование полученного списка в словарь
def dict_factory(cursor, row) -> dict:
    save_dict = {}

    for idx, col in enumerate(cursor.description):
        save_dict[col[0]] = row[idx]

    return save_dict


# Форматирование запроса без аргументов
def update_format(sql, parameters: dict) -> tuple[str, list]:
    values = ", ".join([
        f"{item} = ?" for item in parameters
    ])
    sql += f" {values}"

    return sql, list(parameters.values())


# Форматирование запроса с аргументами
def update_format_where(sql, parameters: dict) -> tuple[str, list]:
    sql += " WHERE "

    sql += " AND ".join([
        f"{item} = ?" for item in parameters
    ])

    return sql, list(parameters.values())


################################################################################
# Создание всех таблиц для БД
def create_dbx():
    with sqlite3.connect(PATH_DATABASE) as con:
        con.row_factory = dict_factory

        ############################################################
        # Создание таблицы с хранением - пользователей
        if len(con.execute("PRAGMA table_info(storage_users)").fetchall()) == 8:
            print("DB was found(1/4)")
        else:
            con.execute(
                ded(f"""
                    CREATE TABLE storage_users(
                        increment INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        user_login TEXT,
                        user_name TEXT,
                        user_surname TEXT,
                        user_fullname TEXT,
                        notif TEXT,
                        user_unix INTEGER
                    )
                """)
            )
            print("DB was not found(1/4) | Creating...")

        # Создание таблицы с хранением - настроек
        if len(con.execute("PRAGMA table_info(storage_settings)").fetchall()) == 2: #!!!!!
            print("DB was found(2/4)")
        else:
            con.execute(
                ded(f"""
                    CREATE TABLE storage_settings(
                        status_work TEXT,
                        status_sched_tenders TEXT
                    )
                """)
            )

            con.execute(
                ded(f"""
                    INSERT INTO storage_settings(
                        status_work,
                        status_sched_tenders
                    )
                    VALUES (?,?)
                """),
                [
                    'True',
                    'True'
                ]
            )
            print("DB was not found(2/4) | Creating...")

        # Создание таблицы с хранением - тендеров
        if len(con.execute("PRAGMA table_info(storage_tenders)").fetchall()) == 5:
            print("DB was found(3/4)")
        else:
            con.execute(
                ded(f"""
                    CREATE TABLE storage_tenders(
                        tender_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tender_name TEXT,
                        tender_link TEXT,
                        date_creat DATE,
                        date_until DATE
                    )
                """)
            )
            print("DB was not found(3/4) | Creating...")

        # Создание таблицы с хранением - товаров
        if len(con.execute("PRAGMA table_info(storage_goods)").fetchall()) == 3:
            print("DB was found(4/4)")
        else:
            con.execute(
                ded(f"""
                    CREATE TABLE storage_goods(
                        good_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        good_name TEXT,
                        tender_id INTEGER REFERENCES storage_tenders(tender_id) ON UPDATE CASCADE
                    )
                """)
            )
            print("DB was not found(4/4) | Creating...")