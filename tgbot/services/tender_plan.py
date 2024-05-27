import os
import glob
import requests
import json
import pandas as pd
import re
from thefuzz import fuzz
from bs4 import BeautifulSoup
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from datetime import datetime
import time
import asyncio
from aiohttp import ClientSession

from tgbot.utils.misc.bot_logging import bot_logger
from tgbot.services.parser_tendors import get_articles


cookies = {
    'jwt': 's%3ABearer%20a4dc57cc44d5ca62a06a7b19660840a66f3048028b417bbc813a1acf6f3691da841b9120373431377409359f64430b0644ee22ddf072fbe6ad656b57eeebe83d.fv8XBqznQBCV2IGatFCIpsqc3upsd40a7AEZa0kaNTg',
    'referer': 'https://tenderplan.ru/app?key=0&tender=6639e01152e24fc13574139f',
    'source': 'key=0&tender=6639e01152e24fc13574139f',
    'tildauid': '1713888711831.359844',
    '__ddg1_': 'ZKa7JlUseYuy3cvawO9W',
}

headers = {
    'Accept': '*/*',
    'Authorization': 'Bearer a4dc57cc44d5ca62a06a7b19660840a66f3048028b417bbc813a1acf6f3691da841b9120373431377409359f64430b0644ee22ddf072fbe6ad656b57eeebe83d',
    'Sec-Fetch-Site': 'same-origin',
    'Accept-Language': 'ru',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Fetch-Mode': 'cors',
    'Host': 'tenderplan.ru',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
    'Connection': 'keep-alive',
    'Referer': 'https://tenderplan.ru/app?key=0&tender=6639e01152e24fc13574139f',
    # 'Cookie': 'jwt=s%3ABearer%20a4dc57cc44d5ca62a06a7b19660840a66f3048028b417bbc813a1acf6f3691da841b9120373431377409359f64430b0644ee22ddf072fbe6ad656b57eeebe83d.fv8XBqznQBCV2IGatFCIpsqc3upsd40a7AEZa0kaNTg; referer=https://tenderplan.ru/app?key=0&tender=6639e01152e24fc13574139f; source=key=0&tender=6639e01152e24fc13574139f; tildauid=1713888711831.359844; __ddg1_=ZKa7JlUseYuy3cvawO9W',
    'Sec-Fetch-Dest': 'empty',
}


# def search_in_tenderplan():
    # https://tenderplan.ru/api/tenders/getlist?q=F-714117
    # https://tenderplan.ru/api/tenders/getlist?page=1&q=Komatsu
    # ...


def get_urls(article = 0):
    urls = []
    if (article == 0): 
        article = get_articles()
        for val in article.iloc:  
            # print(val["Артикул"])      
            for art in val["Артикул"]:
                urls.append({"article": f"{val['Наименование']} / {art}", "art": art, "url": f"https://tenderplan.ru/api/tenders/getlist?q={art}"})
    else:
        articles = article.split(", |,")
        for art in articles:
            urls.append({"article": f"{art}", "url": f"https://tenderplan.ru/api/tenders/getlist?q={art}"})

    return urls


# async def fetch(url, session):
#     st = ''
#     try:
#         async with session.get(url['url']) as response:
#             k = 0
#             st = response.status
#             while response.status != 200:
#                 time.sleep(5)
#                 print('sleeep')
#                 k += 1
#                 if k > 5: break

#             date = response.headers.get("DATE")
#             print(f"{date}:{response.url} with status {response.status}")
#             data = {'url': url, 'response': await response.json()}
#             return data
#     except Exception as e:
#         print(e)
#         bot_logger.error(f"st:{st} --- {e}")


# async def bound_fetch(sem, url, session):
#     # Getter function with semaphore.
#     async with sem:
#         return await fetch(url, session)

async def fetch(url, session, retry_event):
    st = ''
    try:
        async with session.get(url['url']) as response:
            k = 0
            st = response.status
            while response.status == 429:
                await retry_event.wait()  # Ожидаем разрешения продолжения запросов
                async with session.get(url['url']) as response:
                    st = response.status

            while response.status != 200 and k <= 5:
                await asyncio.sleep(5)  # Асинхронная задержка
                print('sleeep')
                k += 1
                async with session.get(url['url']) as response:
                    st = response.status

            if response.status == 200:
                date = response.headers.get("DATE")
                print(f"{date}: {response.url} со статусом {response.status}")
                data = {'url': url, 'response': await response.json()}
                return data
            else:
                print(f"Не удалось получить {url['url']} после {k} попыток")
                return None
    except Exception as e:
        print(e)
        bot_logger.error(f"st: {st} --- {e}")

async def bound_fetch(sem, url, session, retry_event):
    # Функция получения данных с семафором
    async with sem:
        return await fetch(url, session, retry_event)



# async def get_tenders_from_url(tender_state = 1):
#     urls = get_urls(tender_state)
#     return await search_tenders(urls)

# async def get_tenders_from_article(article):
#     urls = get_urls(article = article)
#     return await search_tenders(urls)

def sooup(tenders_id, tenders, res):
    for tender in tenders:
        tend_name = tender.get('orderName')
        tend_id = tender.get('_id')
        submissionCloseDateTime = tender.get('submissionCloseDateTime')
        date_until = datetime.fromtimestamp(submissionCloseDateTime/1000).strftime('%Y-%m-%d')

        price = '-'

        
        # Поиск и вывод файлов
        excel_files = [name for name in glob.glob(f'/Users/zik/Documents/Programs/ParserTenders/tgbot/data/price*.xls*')]
        print(f'excel_files-{excel_files}')

        for file in excel_files:
            print(f'file-{file}')
            # Загрузка Excel файла
            excel_file = file
            df = pd.read_excel(excel_file)

            # Название для поиска
            search_term = res.get("url").get("art")

            # Поиск строк, содержащих текст запроса
            price = df[df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

            # Проверка, найдены ли строки
            if not price.empty:
                print(price)
            else:
                print("Строки, содержащие указанный текст, не найдены")
        
        # for id in tenders_id:
        #     if tend_id in id["id_tender"]:
        #         print("ПОВТОРЕНИЕ")
        #         return tenders_id
        print(tend_id, date_until)
        tenders_id.append({
            "article": res.get('url').get('article'), 
            "price": price,
            "id_tender": tend_id, 
            "url_tender": f"https://tenderplan.ru/app?tender={tend_id}", 
            "date_until": date_until, 
            "tend_name": tend_name,
            # "goods_name": goods_name, 
            # "goods_amount": goods_amount,
            })
        # except Exception as e:
        #     print(e)
        #     pass
    return tenders_id


async def search_in_tenderplan(urls = 0):
    tenders_id = []
    try:
        if urls == 0:
            urls = get_urls()
        else: 
            return 0
        tasks = []
        # create instance of Semaphore
        sem = asyncio.Semaphore(3)
        retry_event = asyncio.Event()
        retry_event.set()  # Устанавливаем событие в начальное состояние

        results = []
        t = time.time()
        # Create client session that will ensure we dont open new connection
        # per each request.
        async with ClientSession(cookies=cookies, headers=headers) as session:
            tasks = [bound_fetch(sem, url, session, retry_event) for url in urls]
            
            while True:
                results1 = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results1:
                    if isinstance(result, Exception):
                        continue
                    if result and result.get('response').get('status') == 429:
                        retry_event.clear()  # Останавливаем отправку запросов при 429
                        await asyncio.sleep(5)  # Ждем некоторое время перед повторной попыткой
                        retry_event.set()  # Разрешаем отправку запросов снова
                if all(result and result['response']['status'] == 200 for result in results if not isinstance(result, Exception)):
                    break  # Завершаем, если все запросы успешны

            # responses = asyncio.gather(*tasks)
            results = results1
        print(time.time()-t)
        print(len(results))
        t1 = time.time()
        for res in results:
            try:
                if res.get('response').get('tenders'):
                    tenders = res.get('response').get('tenders')
                    #pagination
                    # if len(tenders) > 50:
                    #     page = 1
                    #     urls2 = f"https://tenderplan.ru/api/tenders/getlist?page={page}&q={}"
                    #     while len(tenders) > 50:
                    #         response = requests.get(ur)
                    #         soup1 = BeautifulSoup(response.json, "html.parser")
                    #         tenders_id = sooup(soup1, tenders_id, res)
                    ########
                    tenders_id = sooup(tenders_id, tenders, res)
                else:
                    print('tenders none')
                    # bot_logger.error(f"tenders none, скорее всего 429 ошибка")
                    # raise Exception("tenders none")
            except Exception as e:
                print(e)
                bot_logger.error(f"{e}")
        
        print(time.time() - t1)
        for tend in tenders_id:
            print(tend)

        get_excel_from_tenderplan(tenders_id)

        return tenders_id
    except Exception as e:
        print(e)
        get_excel_from_tenderplan(tenders_id)
        bot_logger.error(f"{e}")

def get_excel_from_tenderplan(tenders_id, link = 'tgbot/data/tenders_tenderplan_from_art.xlsx'):
    tends = pd.DataFrame(tenders_id)
    tends.to_excel(link)



######################################--------AUTOPITER-------########################################


def split_search(search_string):
    search_split = []
    digit_count = sum(char.isdigit() for char in search_string)
    if digit_count <= 1:
        return []
    for word in search_string.split(" "):
        digit_count = sum(char.isdigit() for char in word)
        if (
            digit_count >= len(word) // 4
            and len(word)>=6 
            and not(bool(re.search('[а-яА-Я]', word)))

        ):
            search_split.append(word)
    # if bool(re.search(r'\d', good_name)):
    #     continue
    return search_split


def search_in_autopiter(search: str):
    

    params = {
        'detailNumber': search,
        'isFullQuery': 'true',
    }

    try:
        ap_search = search
        resp = requests.get('https://autopiter.ru/api/api/searchdetails', params=params)
        print("response - ", resp.status_code)
        print("good search - ", ap_search)
        goodauto = []

        if resp.status_code == 200:
            params = {'idArticles': [position.get('id') for position in resp.json().get('data').get('catalogs')]}
            get_cost_resp = requests.get('https://autopiter.ru/api/api/appraise/getcosts', params=params)
            print(get_cost_resp)
            
            for position in resp.json().get('data').get('catalogs'):
                # print("position ",position)
                ap_name = position.get('name')
                ap_id = position.get('id')
                ap_number = position.get('number')
                if get_cost_resp.status_code == 200:
                    ap_originalPrice = [cost.get('originalPrice') for cost in get_cost_resp.json().get('data') if cost.get('id') == ap_id and cost.get('originalPrice') > 0]
                    if ap_originalPrice == []: continue
                    else: ap_originalPrice = ap_originalPrice[0]
                else:
                    ap_originalPrice = "--"
                # print("ap_originalPrice  -  ",ap_originalPrice)
                # print("descr совпадение -  ",fuzz.partial_token_sort_ratio(name, descr))
                goodauto.append({
                    'ap_search': ap_search,
                    'ap_name': ILLEGAL_CHARACTERS_RE.sub(r'', ap_name), 
                    'fuzz': fuzz.partial_token_sort_ratio(ap_search, ap_name),
                    'ap_number': ap_number,
                    'ap_originalPrice': ap_originalPrice,
                    'link_autopiter': f"https://autopiter.ru/goods/{ap_number}/{position.get('catalogUrl')}/id{ap_id}",
                    'ap_id': ap_id,
                    })
        elif resp.status_code == 429:
            raise Exception("429")
        if goodauto != []:
            goodauto = pd.DataFrame(goodauto).sort_values(by="fuzz",ascending=False)[:1]
        elif goodauto == []: 
            goodauto = [{
                    'ap_search': '----',
                    'ap_name': '----', 
                    'fuzz': '',
                    'ap_number': '',
                    'ap_originalPrice': '',
                    'link_autopiter': '----',
                    }]
        return goodauto
        # goodsinauto.append(goodsinauto)

            # print("name - ",search_in_autopiter(name))
            # amount = float(g.get("amount"))
            # if tend.get('article').split("/")[1] in name:
            #     goods_name += name + " "
            #     goods_amount += amount
    except Exception as e:
        print(e)
        bot_logger.error(f"{e}")
        return []


def tenders_with_goods(pagecount: int = 1):
    try:
        tenders_with_goods = []
        count = 0
        page = 0
        countn = 50
        while True:
            try:
                params = {'page': page}
                response = requests.get('https://tenderplan.ru/api/tenders/getlist', params=params, cookies=cookies, headers=headers)
                # if (response.json().get('tenders') == []):
                #     break
                if (page>=pagecount):
                    break
                # if (count>countn):
                #     break
                page += 1
                tenders = response.json().get('tenders')
                print(f"--------{len(tenders)}")
                for tend in tenders:
                    try:
                        tend_name = tend.get('orderName')
                        id = tend.get('_id')
                        print(f"tender  --  {tend_name}  --  {id}")
                        params = {
                            'id': id,
                        }
                        response = requests.get('https://tenderplan.ru/api/tenders/get', params=params, cookies=cookies, headers=headers)
                        if "ObjectInfo" in response.json().get('json'):
                            goods = json.loads(response.json().get('json'))["0"]["fv"]["0"]["fv"]["tb"]
                            submission_close_timestamp = int(json.loads(response.json().get('json'))['1']['fv']['1']['fv'])
                            print(submission_close_timestamp)
                            submission_close_datetime = datetime.fromtimestamp(submission_close_timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
                            for good in goods:
                                # if (count>countn):
                                #     break
                                good_name = goods.get(good).get('0').get('fv')
                                print(f"name - {good_name}")
                                # count += 1
                                
                                for name in split_search(good_name):
                                    ap_search = search_in_autopiter(name)
                                    for ap_s in ap_search.iterrows():
                                        # print(ap_s)
                                        count += 1
                                        print("count",count)
                                        tenders_with_goods.append({
                                            "tend_name": tend_name,
                                            "tend_link": f"https://tenderplan.ru/app?tender={id}",
                                            "tend_under": submission_close_datetime,
                                            "good_name": good_name,
                                            "ap_good_name": name,
                                            "ap_search_name": ap_s[1].get('ap_name'),
                                            "ap_search_fuzz": ap_s[1].get('fuzz'),
                                            "ap_search_link": ap_s[1].get('link_autopiter'),
                                            "ap_id": ap_s[1].get('ap_id'),
                                            "ap_search_price": ap_s[1].get('ap_originalPrice'),
                                        })
                            # break
                    except Exception as e1:
                        print("error -- ",e1)
                        bot_logger.error(f"{e1}")
            except Exception as e:
                print(e)
                bot_logger.error(f"{e}")
        print(f"count - {count}")

        # for twg in tenders_with_goods:
        #     print(twg)

        print(f"excel!!!!!!!!!")
        tenders_with_goods = get_all_price(tenders_with_goods)
        tends = pd.DataFrame(tenders_with_goods)
        tends.to_excel(r'tgbot/data/tenders_with_goods.xlsx')
        print(f"excel!!!!!!!!!2")


        return tenders_with_goods
    except Exception as e:
        print(e)
        bot_logger.error(f"{e}")


def get_all_price(tenders_with_goods):
    ap_ids = []
    c = 0
    tenders_with_goods2 = []
    for ap in tenders_with_goods:
        ap_ids.append(ap.get('ap_id'))
    
    params = {'idArticles': ap_ids}
    get_cost_resp = requests.get('https://autopiter.ru/api/api/appraise/getcosts', params=params)
    while get_cost_resp.status_code == 429:
        time.sleep(5)
        c += 1
        get_cost_resp = requests.get('https://autopiter.ru/api/api/appraise/getcosts', params=params)
        if c>10: break

    print(get_cost_resp.status_code)
    cost_resp = get_cost_resp.json().get('data')
    for ap in tenders_with_goods:
        try:
            id = ap.get("ap_id")
            cost = [cost.get('originalPrice') for cost in cost_resp if cost.get('id') == id]
            
            if cost:
                ap['ap_search_price'] = cost[0]
            tenders_with_goods2.append(ap)
        except Exception as e:
            print(e)
            bot_logger.error(f"{e}")
    return tenders_with_goods2


def beautitext(text: str):

    # texts = re.findall(r'\w', text)

    tt = []

    texts = text.split(" ")
    for te in texts:
        digit_count = sum(char.isdigit() for char in te)
        if digit_count >= len(te) // 2:
            tt.append(te)
        # if bool(re.search(r'\d', te)):
        #     tt.append(te)


    return str(tt)

# print(beautitext('Помпа ЗМЗ-406, 409 /Евро-3, Евро-4'))
# tenders_with_goods()



# print(search_in_autopiter('Форсунка топливная Common Rail КАМАЗ'))






# curl 'https://tenderplan.ru/api/tenders/getlist?' \
# -X 'GET' \
# -H 'Accept: */*' \
# -H 'Authorization: Bearer f7dcac67acdb2a348f5c81fc26cfafaba892a7bc02dceb97ffe079ad60b0edb4399522590c067b24459b785fa019006943700cc47033ca26b7aecd22f3777077' \
# -H 'Sec-Fetch-Site: same-origin' \
# -H 'Accept-Language: ru' \
# -H 'Accept-Encoding: gzip, deflate, br' \
# -H 'Sec-Fetch-Mode: cors' \
# -H 'Host: tenderplan.ru' \
# -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15' \
# -H 'Referer: https://tenderplan.ru/app?key=0&tender=6628ae9952e24fc13583dd05' \
# -H 'Connection: keep-alive' \
# -H 'Cookie: jwt=s%3ABearer%20f7dcac67acdb2a348f5c81fc26cfafaba892a7bc02dceb97ffe079ad60b0edb4399522590c067b24459b785fa019006943700cc47033ca26b7aecd22f3777077.UH%2BcCzOylTzLr%2BF6Hf4kerem6GuMoVK%2FBSiOYmPCkEc; source=key=0&tender=6628ae9952e24fc13583dd05; previousUrl=tenderplan.ru%2Fbitrix24%2Finstructions%2F; tildasid=1713941269630.966260; tildauid=1713888711831.359844; referer=https://tenderplan.ru/app; __ddg1_=ZKa7JlUseYuy3cvawO9W' \
# -H 'Sec-Fetch-Dest: empty' \
# -H 'Socket: ZTvzcuitnjsM-m4OBCP4'