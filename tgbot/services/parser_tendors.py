import requests
from bs4 import BeautifulSoup
import asyncio
from aiohttp import ClientSession
import pandas as pd
from time import time
import os, sys; sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from tgbot.data.config import PATH_EXCEL
from tgbot.utils.misc.bot_logging import bot_logger



# arrt = [
#     {'Name': 'О-514002', 'articles': ['О-514002', 'JX0818', '61000070005', '3831236', 'W 962/6', 'OP592', 'C-6204']},
#     {'Name': 'F-714117', 'articles': ['F-714117', '612630080087', 'FC-71090', 'R010018']},
#     {'Name': 'F-742003', 'articles': ['F-742003', '612630080088', 'PL420', 'VG1540080032', 'A 960 477 00 03', 'PL 420/7X', 'SFC-7939-30B']},
#     {'Name': 'F-742003X', 'articles': ['F-742003X', '612630080088', 'PL420 с подогревом', 'VG1540080032', 'A960 477 00 03','PL 420/7X', 'SFC-7939-30B']},
# ]

# article = {
#         'О-514002': ['О-514002', 'JX0818', '61000070005', '3831236', 'W 962/6', 'OP592', 'C-6204'],
#         'F-714117': ['F-714117', '612630080087', 'FC-71090', 'R010018'],
#         'F-742003': ['F-742003', '612630080088', 'PL420', 'VG1540080032', 'A 960 477 00 03', 'PL 420/7X', 'SFC-7939-30B'],
#         'F-742003X': ['F-742003X', '612630080088', 'PL420 с подогревом', 'VG1540080032', 'A960 477 00 03','PL 420/7X', 'SFC-7939-30B'],
#        } 

# art1 = {
#         'F-714117': ['612630080087', 'FC-71090', 'R010018'],
#         'F-742003': ['612630080088', 'PL420', 'VG1540080032'],
#        } 


# def get_articles():
#     link = PATH_EXCEL
#     art = pd.read_excel(link, skiprows=1)
#     art = art.loc[:,["Наименование Wanlanda","Наименование аналога"]]
#     art["Наименование аналога"] = art["Наименование аналога"].str.split(", |,")
#     for a in art.iloc:
#         a["Наименование аналога"].append(a["Наименование Wanlanda"])
#     return art

def get_articles(link = PATH_EXCEL):
    # link = PATH_EXCEL
    all_article = pd.DataFrame(index=[], columns=['Наименование', 'Артикул'])
    excel_reader = pd.ExcelFile(link)
    for sheet_name in excel_reader.sheet_names:
        exc = excel_reader.parse(sheet_name, usecols=['Наименование', 'Артикул'])
        exc['Наименование'] = sheet_name + " / " + str(exc['Наименование'].values)  # добавление названия листа к наименованию позиции
        all_article = pd.concat([all_article,exc], ignore_index=True)
    all_article = all_article.dropna(inplace=False)    
    all_article["Артикул"] = all_article["Артикул"].astype(str)
    all_article["Артикул"] = all_article["Артикул"].str.split(", | ,")
    # for a in art.iloc:
    #     a["Артикул"].append(a["Наименование"])
    # print(f"колич артик:{len(all_article)}")
    bot_logger.warning(f"колич артик:{len(all_article)}")
    print(f"all_article: {all_article[:2]}")
    return all_article[:]

# для pd
def get_urls(tender_state = 1, article = 0):
    # tender_state = 1:открытые 100:все
    urls = []
    if (article == 0): 
        article = get_articles()
        for val in article.iloc:  
            # print(val["Артикул"])      
            for art in val["Артикул"]:
                urls.append({"article": f"{val['Наименование']}/{art}", "url": f"http://www.tender.pro/api/tenders/list?&good_name={art}&tender_state={tender_state}&by=1000"})
    else:
        articles = article.split(", |,")
        for art in articles:
            urls.append({"article": f"{art}", "url": f"http://www.tender.pro/api/tenders/list?&good_name={art}&tender_state={tender_state}&by=1000"})

    return urls


async def fetch(url, session):
    async with session.get(url['url']) as response:
        status = response.status
        date = response.headers.get("DATE")
        print(f"{date}:{response.url} with status {status}")
        data = {'url': url, 'response': await response.text()}
        return data


async def bound_fetch(sem, url, session):
    # Getter function with semaphore.
    async with sem:
        return await fetch(url, session)


# def get_tenders_from_url1():
#     urls = get_urls()
#     tenders_id = []
#     for url in urls:
#         response = requests.get(url["url"])
#         soup = BeautifulSoup(response.content, "html.parser")
#         for tender in soup.find_all("td", class_="tender__id"):
#             id_tender = tender.text
#             print(id_tender + str(url["article"]))
#             tenders_id.append({"article": url["article"], "id_tender": id_tender, "url_tender": f"https://www.tender.pro/api/tender/{id_tender}/view_public"})
#     return tenders_id


async def get_tenders_from_url(tender_state = 1):
    urls = get_urls(tender_state)
    return await search_tenders(urls)

async def get_tenders_from_article(article):
    urls = get_urls(article = article)
    return await search_tenders(urls)


def sooup(soup, tenders_id, res):
    for tender in soup.find_all("tr", class_="table-stat__row"):
        try:
            id_tender = tender.find("td", class_="tender__id").text
            date_tender = tender.find("td", class_="tender__untill").text
        except Exception:
            continue
        # if id_tender == None:
        #     continue
        # id_tender = id_tender.text
        for id in tenders_id:
            if id_tender in id["id_tender"]:
                print("ПОВТОРЕНИЕ")
                return tenders_id
        print(id_tender, date_tender)
        # resp = requests.get(f"http://www.tender.pro/api/_tender.item.json?_key=1732ede4de680a0c93d81f01d7bac7d1&company_id=1&id={id_tender}")
        # try:
        #     goods = resp.json().get("result").get("data")
        #     goods_name = ""
        #     goods_amount = 0
        #     for g in goods:
        #         name = g.get("name")
        #         amount = float(g.get("amount"))
        #         if res['url']['article'].split("/")[1] in name:
        #             goods_name += name + " "
        #             goods_amount += amount
        tenders_id.append({
            "article": res['url']['article'], 
            "id_tender": id_tender, 
            "date_until": date_tender, 
            "url_tender": f"https://www.tender.pro/api/tender/{id_tender}/view_public", 
            # "goods_name": goods_name, 
            # "goods_amount": goods_amount,
            })
        # except Exception as e:
        #     print(e)
        #     pass
    return tenders_id


async def search_tenders(urls):
    tasks = []
    # create instance of Semaphore
    sem = asyncio.Semaphore(5)
    results = []
    t = time()
    # Create client session that will ensure we dont open new connection
    # per each request.
    async with ClientSession() as session:
        for url in urls:
            # pass Semaphore and session to every GET request
            task = asyncio.ensure_future(bound_fetch(sem, url, session))
            tasks.append(task)

        responses = asyncio.gather(*tasks)
        results = await responses
    print(time()-t)
    print(len(results))
    t1 = time()
    tenders_id = []
    for res in results:
        soup = BeautifulSoup(res["response"], "html.parser")   
        pag = soup.find("div", class_="pagination-pages")
        print(f"pag: {pag}")
        if (pag != None):
            print(f"pag: {str(pag)[44:45]}")
            pages = int(str(pag)[44:45])
            urls2 = []
            for i in range(pages):
                urls2.append(f"{res['url']['url']}&page={i}")
            print(urls2)
            for ur in urls2:
                response = requests.get(ur)
                soup1 = BeautifulSoup(response.content, "html.parser")
                tenders_id = sooup(soup1, tenders_id, res)
        tenders_id = sooup(soup, tenders_id, res)
    
    print(time() - t1)
    for tend in tenders_id:
        print(tend)

    return tenders_id

def get_excel_from_tenders(tenders_id, link = 'tgbot/data/tenders_id_all.xlsx'):
    tends = pd.DataFrame(tenders_id)
    tends.to_excel(link)



# https://www.tender.pro/api/tender/876455/view_public

# urls = get_urls1(article)
# tenders_id = get_tenders_from_url(urls)
# for tend in tenders_id:
#     print(tend)



# zik@MacBook-Air-Ila парсер % /usr/local/bin/python3 /Users/zik/Documents/Programs/парсер/parser_tendors.py
# 876455F-714117/612630080087
# 878638F-742003/PL420
# {'article': 'F-714117/612630080087', 'id_tender': '876455'}
# {'article': 'F-742003/PL420', 'id_tender': '878638'}


# http://www2.tender.pro/api/tenders/list?sid=15932209&company_id=415538&face_id=440662&order=3&tmpl-opts=%22company_id%3A415538%22%2C%22face_id%3A440662%22%2C%22order%3A3%22%2C%22view_tenders_list-tmpl-signup%3A1%22%2C%22filter_reset%3A1%22%2C%22view_tenders_list-tmpl-name%3A%22%2C%22view_tenders_list-tmpl-default%3A%22%2C%22tender_id%3A%22%2C%22tender_name%3A%22%2C%22company_name%3A%22%2C%22good_name%3ASFC-7939-30B%22%2C%22tender_type%3A100%22%2C%22tender_state%3A1%22%2C%22tender_interest_type%3A%22%2C%22tender_invited%3A%22%2C%22country%3A0%22%2C%22region%3A%22%2C%22basis%3A0%22%2C%22tender_show_own%3A0%22%2C%22okved%3A%22%2C%22dateb%3A%22%2C%22datee%3A%22%2C%22dateb2%3A%22%2C%22datee2%3A%22%2C%22by%3A25%22&view_tenders_list-tmpl-signup=1&filter_tmpl=0&filter_reset=1&view_tenders_list-tmpl-name=&view_tenders_list-tmpl-default=&tender_id=&tender_name=&company_name=&good_name=VG1540080032&tender_type=100&tender_state=1&tender_interest_type=&tender_invited=&country=0&region=&basis=0&tender_show_own=0&okved=&dateb=&datee=&dateb2=&datee2=&by=25
# http://www.tender.pro/api/_tender.info.json?_key=1732ede4de680a0c93d81f01d7bac7d1&company_id=44441&id=144276

# https://www.tender.pro/api/tenders/list?sid=
#     &company_id=
#     &face_id=0
#     &order=3
#     &tender_id=
#     &tender_name=
#     &company_name=
#     &good_name=PL+420
#     &tender_type=100
#     &tender_state=100
#     &country=0
#     &region=
#     &basis=0
#     &okved=
#     &dateb=&datee=&dateb2=&datee2=

# PL420

# https://www.tender.pro/api/tenders/list?&good_name=PL420&tender_state=100
