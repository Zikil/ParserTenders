import requests
import json
import pandas as pd
import re
from thefuzz import fuzz, process
from bs4 import BeautifulSoup
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from datetime import datetime
import time

from tgbot.utils.misc.bot_logging import bot_logger

cookies = {
    'jwt': 's%3ABearer%20...',
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
    'Sec-Fetch-Mode': 'cors',
    'Host': 'tenderplan.ru',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15',
    'Connection': 'keep-alive',
    'Referer': 'https://tenderplan.ru/app?key=0&tender=6639e01152e24fc13574139f',
    'Sec-Fetch-Dest': 'empty',
}

def clean_text(text):
    return re.sub(r'[^\w\s]', '', text).lower()

def split_search(search_string):
    search_split = []
    digit_count = sum(char.isdigit() for char in search_string)
    if digit_count <= 1:
        return []
    for word in search_string.split(" "):
        digit_count = sum(char.isdigit() for char in word)
        if digit_count >= len(word) // 4 and len(word) >= 6 and not re.search('[а-яА-Я]', word):
            search_split.append(word)
    return search_split

def search_in_autopiter(search):
    params = {'detailNumber': search, 'isFullQuery': 'true'}
    try:
        resp = requests.get('https://autopiter.ru/api/api/searchdetails', params=params)
        goodauto = []

        if resp.status_code == 200:
            params = {'idArticles': [position.get('id') for position in resp.json().get('data').get('catalogs')]}
            get_cost_resp = requests.get('https://autopiter.ru/api/api/appraise/getcosts', params=params)
            
            for position in resp.json().get('data').get('catalogs'):
                ap_name = position.get('name')
                ap_id = position.get('id')
                ap_number = position.get('number')
                if get_cost_resp.status_code == 200:
                    ap_originalPrice = next((cost.get('originalPrice') for cost in get_cost_resp.json().get('data') if cost.get('id') == ap_id and cost.get('originalPrice') > 0), "--")
                else:
                    ap_originalPrice = "--"
                goodauto.append({
                    'ap_search': search,
                    'ap_name': ILLEGAL_CHARACTERS_RE.sub(r'', ap_name), 
                    'fuzz': fuzz.partial_token_sort_ratio(search, ap_name),
                    'ap_number': ap_number,
                    'ap_originalPrice': ap_originalPrice,
                    'link_autopiter': f"https://autopiter.ru/goods/{ap_number}/{position.get('catalogUrl')}/id{ap_id}",
                    'ap_id': ap_id,
                })
        elif resp.status_code == 429:
            raise Exception("429")
        if goodauto:
            goodauto = pd.DataFrame(goodauto).sort_values(by="fuzz", ascending=False)[:1]
        else:
            goodauto = [{
                'ap_search': '----',
                'ap_name': '----', 
                'fuzz': '',
                'ap_number': '',
                'ap_originalPrice': '',
                'link_autopiter': '----',
            }]
        return goodauto
    except Exception as e:
        bot_logger.error(f"{e}")
        return []

def tenders_with_goods(pagecount=1):
    try:
        tenders_with_goods = []
        page = 0

        while page < pagecount:
            params = {'page': page}
            response = requests.get('https://tenderplan.ru/api/tenders/getlist', params=params, cookies=cookies, headers=headers)
            tenders = response.json().get('tenders')
            page += 1

            for tend in tenders:
                tend_name = tend.get('orderName')
                id = tend.get('_id')
                params = {'id': id}
                response = requests.get('https://tenderplan.ru/api/tenders/get', params=params, cookies=cookies, headers=headers)
                if "ObjectInfo" in response.json().get('json'):
                    goods = json.loads(response.json().get('json'))["0"]["fv"]["0"]["fv"]["tb"]
                    submission_close_timestamp = int(json.loads(response.json().get('json'))['1']['fv']['1']['fv'])
                    submission_close_datetime = datetime.fromtimestamp(submission_close_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')

                    for good in goods.values():
                        good_name = good.get('0').get('fv')
                        for name in split_search(good_name):
                            ap_search = search_in_autopiter(name)
                            for ap_s in ap_search.iterrows():
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
        tenders_with_goods = get_all_price(tenders_with_goods)
        tends = pd.DataFrame(tenders_with_goods)
        tends.to_excel('tgbot/data/tenders_with_goods.xlsx')

        return tenders_with_goods
    except Exception as e:
        bot_logger.error(f"{e}")

def get_all_price(tenders_with_goods):
    ap_ids = [ap.get('ap_id') for ap in tenders_with_goods]
    params = {'idArticles': ap_ids}
    get_cost_resp = requests.get('https://autopiter.ru/api/api/appraise/getcosts', params=params)
    
    retry_count = 0
    while get_cost_resp.status_code == 429 and retry_count < 10:
        time.sleep(5)
        retry_count += 1
        get_cost_resp = requests.get('https://autopiter.ru/api/api/appraise/getcosts', params=params)

    if get_cost_resp.status_code == 200:
        cost_resp = get_cost_resp.json().get('data')
        for ap in tenders_with_goods:
            id = ap.get("ap_id")
            cost = next((cost.get('originalPrice') for cost in cost_resp if cost.get('id') == id), None)
            if cost:
                ap['ap_search_price'] = cost

    return tenders_with_goods

def beautitext(text):
    texts = text.split(" ")
    tt = [te for te in texts if sum(char.isdigit() for char in te) >= len(te) // 2]
    return str(tt)
