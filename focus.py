
from google.cloud import firestore


# 初始化 Firestore 資料庫客戶端
firestore_client = firestore.Client.from_service_account_json('stockapi.json')
# 指定 Firestore 中的 'stockDB' 集合 (Collection)
collection = firestore_client.collection('stockDB')


def checktime(stock_codes,user_id):
    #
    user = collection.document(user_id).get().to_dict()
    if 'timehis' in user:
        list = user['timehis']
    else:
        list = []
    list.append(stock_codes)
    collection.document(user_id).set( {'timehis': list}, merge=True)

def replyitem(user_id):
    #取得user資料
    user = collection.document(user_id).get().to_dict()
    #先做保險取值，如果有查詢的紀錄就拿回查詢紀錄，不然放空list
    if 'timehis' in user:
        list = user['timehis']
    else:
        list = []
    #產生計算用空字典
    counts_dict = {}
    for item in list:
        counts_dict[item] = counts_dict.get(item, 0) + 1
    #將將字典內容按照「數值 (Value)」由大到小排序，並轉換成一個列表(每格會是一個元組)
    sorted_items = sorted(counts_dict.items(), key=lambda item: item[1], reverse=True)
    backlist = []
    count = 0
    for item in sorted_items:
        #取出元組的鍵，放入backlist裡
        backlist.append(item[0])
        count += 1
        if count == 4:
            break
    #print(backlist)
    return backlist
