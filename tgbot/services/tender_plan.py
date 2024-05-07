import requests
import json
import pandas as pd
import re
from thefuzz import fuzz
from bs4 import BeautifulSoup
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from datetime import datetime

cookies = {
    'jwt': 's%3ABearer%20f7dcac67acdb2a348f5c81fc26cfafaba892a7bc02dceb97ffe079ad60b0edb4399522590c067b24459b785fa019006943700cc47033ca26b7aecd22f3777077.UH%2BcCzOylTzLr%2BF6Hf4kerem6GuMoVK%2FBSiOYmPCkEc',
    'source': 'key=0&tender=6628ae9952e24fc13583dd05',
    'previousUrl': 'tenderplan.ru%2Fbitrix24%2Finstructions%2F',
    'tildasid': '1713941269630.966260',
    'tildauid': '1713888711831.359844',
    'referer': 'https://tenderplan.ru/app',
    '__ddg1_': 'ZKa7JlUseYuy3cvawO9W',
}

headers = {
    'Accept': '*/*',
    'Authorization': 'Bearer f7dcac67acdb2a348f5c81fc26cfafaba892a7bc02dceb97ffe079ad60b0edb4399522590c067b24459b785fa019006943700cc47033ca26b7aecd22f3777077',
    'Sec-Fetch-Site': 'same-origin',
    'Accept-Language': 'ru',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Sec-Fetch-Mode': 'cors',
    'Host': 'tenderplan.ru',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Referer': 'https://tenderplan.ru/app?key=0&tender=6628ae9952e24fc13583dd05',
    'Connection': 'keep-alive',
    # 'Cookie': 'jwt=s%3ABearer%20f7dcac67acdb2a348f5c81fc26cfafaba892a7bc02dceb97ffe079ad60b0edb4399522590c067b24459b785fa019006943700cc47033ca26b7aecd22f3777077.UH%2BcCzOylTzLr%2BF6Hf4kerem6GuMoVK%2FBSiOYmPCkEc; source=key=0&tender=6628ae9952e24fc13583dd05; previousUrl=tenderplan.ru%2Fbitrix24%2Finstructions%2F; tildasid=1713941269630.966260; tildauid=1713888711831.359844; referer=https://tenderplan.ru/app; __ddg1_=ZKa7JlUseYuy3cvawO9W',
    'Sec-Fetch-Dest': 'empty',
    'Socket': 'ZTvzcuitnjsM-m4OBCP4',
}

def search_in_autopiter(search: str):
    cookies = {
        'guestId': '0_3IPr7jh-WiY0mUjEdAk',
        'app_state': '{%22cart%22:{%22enteredComment%22:%22%22%2C%22sort%22:%22none%22%2C%22selectedDetailUids%22:[]%2C%22selectedDeliveryType%22:%221%22%2C%22cartViewMode%22:0}%2C%22appraiseProduct%22:{%22appraiseCardOpenState%22:0}%2C%22ordersInfo%22:{%22ordersInfo%22:{%22disabledColumns%22:null}}%2C%22user%22:{%22confirmCity%22:false%2C%22isWholesaleWidgetOpen%22:false%2C%22mobileMenuListToggle%22:{}%2C%22newSiteLoyalty%22:false}%2C%22mobileVersion%22:{%22isMobileDevice%22:false}%2C%22abTest%22:[]%2C%22server%22:{%22domainDebug%22:%22%22}}',
    }

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Sec-Fetch-Site': 'same-origin',
        # 'Cookie': 'guestId=0_3IPr7jh-WiY0mUjEdAk; app_state={%22cart%22:{%22enteredComment%22:%22%22%2C%22sort%22:%22none%22%2C%22selectedDetailUids%22:[]%2C%22selectedDeliveryType%22:%221%22%2C%22cartViewMode%22:0}%2C%22appraiseProduct%22:{%22appraiseCardOpenState%22:0}%2C%22ordersInfo%22:{%22ordersInfo%22:{%22disabledColumns%22:null}}%2C%22user%22:{%22confirmCity%22:false%2C%22isWholesaleWidgetOpen%22:false%2C%22mobileMenuListToggle%22:{}%2C%22newSiteLoyalty%22:false}%2C%22mobileVersion%22:{%22isMobileDevice%22:false}%2C%22abTest%22:[]%2C%22server%22:{%22domainDebug%22:%22%22}}',
        'Sec-Fetch-Dest': 'empty',
        'Accept-Language': 'ru',
        'Sec-Fetch-Mode': 'cors',
        'Host': 'autopiter.ru',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Referer': 'https://autopiter.ru/goods/%D1%84%D0%BE%D1%80%D1%81%D1%83%D0%BD%D0%BA%D0%B0%20%D1%82%D0%BE%D0%BF%D0%BB%D0%B8%D0%B2%D0%BD%D0%B0%D1%8F%20common%20rail%20%D0%BA%D0%B0%D0%BC%D0%B0%D0%B7',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }

    params = {
        'detailNumber': search,
        'isFullQuery': 'true',
    }

    try:
        ap_search = search
        resp = requests.get('https://autopiter.ru/api/api/searchdetails', params=params, cookies=cookies, headers=headers)
        print("response - ", resp.status_code)
        print("good search - ", ap_search)
        goodauto = []

        if resp.status_code == 200:
            params = {'idArticles': [position.get('id') for position in resp.json().get('data').get('catalogs')]}
            get_cost_resp = requests.get('https://autopiter.ru/api/api/appraise/getcosts', params=params, cookies=cookies, headers=headers)
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
                    })
        elif resp.status_code == 429:
            raise Exception("429")
        if goodauto != []:
            goodauto = pd.DataFrame(goodauto).sort_values(by="fuzz",ascending=False)[:2]
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
        return []


def tenders_with_goods(pagecount = 1):
    try:

        tenders_with_goods = []

        count = 0
        page = 0

        while True:
            try:
                params = {'page': page}
                response = requests.get('https://tenderplan.ru/api/tenders/getlist', params=params, cookies=cookies, headers=headers)
                # if (response.json().get('tenders') == []):
                #     break
                if (page>=pagecount):
                    break
                
                page += 1
                tenders = response.json().get('tenders')
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
                            ###
                            submission_close_timestamp = int(json.loads(response.json().get('json'))['1']['fv']['1']['fv'])
                            print(submission_close_timestamp)
                            # submission_close_datetime = datetime.fromtimestamp(submission_close_timestamp)#.fromtimestamp(submission_close_timestamp / 1000)
                            # submission_close_datetime = datetime.datetime.strftime(submission_close_timestamp, '%d/%m/%Y')
                            submission_close_datetime = datetime.fromtimestamp(submission_close_timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
                            for good in goods:
                                count += 1
                                # if (count>50):
                                #     break
                                good_name = goods.get(good).get('0').get('fv')
                                # print(f"name - {good_name}")
                                ap_search = search_in_autopiter(good_name)
                                for ap_s in ap_search.iterrows():
                                    # print(ap_s)
                                    tenders_with_goods.append({
                                        "tend_name": tend_name,
                                        "tend_link": f"https://tenderplan.ru/app?tender={id}",
                                        "tend_under": submission_close_datetime,
                                        "good_name": good_name,
                                        "ap_search_fuzz": ap_s[1].get('ap_name'),
                                        "ap_search_name": ap_s[1].get('fuzz'),
                                        "ap_search_link": ap_s[1].get('link_autopiter'),
                                        "ap_search_price": ap_s[1].get('ap_originalPrice'),
                                    })
                            # break
                    except Exception as e:
                        print("error -- ",e)

            except Exception as e:
                print("errror - ",e)
        print(f"count - {count}")

        for twg in tenders_with_goods:
            print(twg)

        tends = pd.DataFrame(tenders_with_goods)
        tends.to_excel(r'tgbot/data/tenders_with_goods.xlsx')

        return tenders_with_goods
    except Exception as e:
        print(e)


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