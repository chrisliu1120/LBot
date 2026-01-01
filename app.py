from google.cloud import firestore
from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    QuickReply,      #快速覆回覆要加入
    QuickReplyItem,  #快速覆回覆要加入
    MessageAction,   #快速覆回覆要加入
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    FollowEvent,
    UnfollowEvent,
    TextMessageContent
)


from stock import stockprice
from focus import checktime, replyitem
import time
import requests
import json
import os



with open('env.json', encoding='utf-8') as f: #把env檔讀進來
    env = json.load(f)

with open('TSEno.json', encoding='utf-8') as f: #把上市代碼檔讀進來
    TSEno = json.load(f)

with open('OTCno.json', encoding='utf-8') as f: #把上市代碼檔讀進來
    OTCno = json.load(f)

# 初始化 Firestore 資料庫客戶端
firestore_client = firestore.Client.from_service_account_json('stockapi.json')
# 指定 Firestore 中的 'stockDB' 集合 (Collection)
collection = firestore_client.collection('stockDB')




#LINEBOT SDK
app = Flask(__name__)


configuration = Configuration(access_token = env.get('ACCESS_TOKEN'))
handler = WebhookHandler(env.get('CHANNEL_SECRET'))


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    print(event.message.text)
    print(event.source.user_id)
    messages = []

    # 提取 user_id
    user_id = event.source.user_id
    # 提取 text(使用者輸入的股票代號)
    stock_codes = event.message.text

    if stock_codes == 'q':
        text = '下面是你常查詢的四檔股票'
        reply = replyitem(user_id)
        items = []                        #創建一個空list

        for item in reply:
            item = QuickReplyItem(action=MessageAction(label = item,text = item))
            items.append(item)

        quick_reply = QuickReply(items=items)
        messages.append(TextMessage(text=text, quick_reply=quick_reply))

    # 執行查詢股價函式&紀錄查詢次數
    else:
        if stock_codes in TSEno or OTCno:
            checktime(stock_codes, user_id)  #紀錄股票查詢計次的函式
        retext = stockprice(stock_codes)
        messages.append(TextMessage(text=retext))

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        profile = dict(line_bot_api.get_profile(event.source.user_id))
        display = profile.get('display_name') or 'NA'
        picture_url = profile.get('picture_url')
        # 將使用者資料更新，使用 merge=True 避免覆蓋現有資料
        collection.document(event.source.user_id).set({'display_name':display} | {'picture_url': picture_url}, merge=True) #
        #
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                #messages=[TextMessage(text=retext)]
                messages=messages
            )
        )


#加入的紀錄程式
@handler.add(FollowEvent)
def handle_message(event):
    print(event.source.user_id)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        profile = dict(line_bot_api.get_profile(event.source.user_id))
        display = profile.get('display_name') or 'NA'
        welcome = f'Welcome {display}'

        collection.document(event.source.user_id).set(profile | {'follow': time.strftime('%Y/%m/%d-%H:%M:%S')}, merge=True)

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=welcome)]
            )
        )

#退出的紀錄程式
@handler.add(UnfollowEvent)
def handle_message(event):
    print(event.source.user_id)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        collection.document(event.source.user_id).update({'unfollow': time.strftime('%Y/%m/%d-%H:%M:%S')})


#首頁訊息，測試是否上線
@app.route("/")
def index():
    return "<h1>你看不見我</h1>"




if __name__ == "__main__":
    app.run(host="0.0.0.0",port=6880, debug=True)
