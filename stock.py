import time
import requests
'''
這是一個股票檔案
'''
# 查詢股價進入點
def stockprice(stock_codes):
    codeno = f'tse_{stock_codes}.tw'
    timestamp = int(time.time() * 1000)
    api_url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?json=1&ex_ch={codeno}"
    rate = requests.get(api_url)
    req = rate.json()
    stock_data = req['msgArray']

    # --- 取值邏輯 ---
    code = stock_data[0].get('c')
    name = stock_data[0].get('n')
    price = stock_data[0].get('z', '-')
    bid_price = stock_data[0].get('b', '_').split('_')[0]
    yesterday_price = stock_data[0].get('y', '-')
    source = "(成交)"
    vol = stock_data[0].get('v', 'N/A')
    # --- 價格取值邏輯 ---
    if price == '-':
        if bid_price and bid_price != '-':
            price = bid_price
            source = "(委買)"
        elif yesterday_price and yesterday_price != '-':
            price = yesterday_price
            source = "(昨收)"
    price_int = price[0:-2]                 #prince值為字串，所以取到倒數兩位數
    # --- 漲跌計算邏輯 ---
    change = "N/A"
    percentage = "N/A"
    updown = "N/A"
    if yesterday_price != '-' and price != '-':
        change_val = float(price) - float(yesterday_price)
        if change_val > 0:
            updown = "▲"
        elif change_val < 0:
            updown = "▼"
        elif change_val == 0:
            updown = "--"

        percentage_val = (change_val / float(yesterday_price)) * 100
        change = f"{change_val:+.2f}"
        percentage = f"{percentage_val:+.2f}%"
    quotes = {}
    quotes = {
        '股票代碼': code,
        '公司簡稱': stock_data[0].get('n', 'N/A'),
        '成交價': price_int,
        '來源': source,
	'漲跌':updown,
        '成交量': vol,
            }
    text = f"{name}\n最新成交價:{price_int}{source}\n{updown}漲跌:{change}＊漲跌幅:{percentage}\n成交量:{vol}"
    return text

