import codecs
import re
from Tools import get_html,ALL_CONFIG
import time
import pytz
import random
from datetime import datetime,timedelta
from Tools.AMAZON_API.amazon_api.Amazon_api import Amazon_MWS,Amazon_AWS
from multiprocessing import Pool,Lock

#把list洗乱
def shuffle_list(list_name):

    from random import shuffle
    shuffle(list_name)
    # 返回随机排序后的序列
    return list_name

'''Amazon API'''
def get_product_infos(asins,fail_url):
    global fr
    # global ferr
    fr = open(ALL_CONFIG.AMAZON_RESULT_FILE, 'aw')
    result = amazon_aws.get_product_info(asins)

    # result_dict = result
    if result['result']:
        # print result['data']
        fr.write(str(result['data'])+'\n')
        result_dict = result['data']
    else:
        print ('not', str(result['error_message']))
        # ferr.write(str(asins) + '\t' + str(result['error_message']) + '\n')
        with open(ALL_CONFIG.AMAZON_FAIL_URL_FILE,'aw') as fail_url:
            fail_url.write(fail_url+'\n')
        result_dict = {}
    return result_dict

# def start_api(asin_itemsId):
#     # with open('./Result/items_asin.txt', 'r') as f:
#     #     a = f.readlines()
#     #     N = 10
#     #     b = [a[i:i + N] for i in range(0, len(a) + 1, N)]
#     #     for ls in b:
#     #         get_product_infos(ls)
#     api_dict = get_product_infos(asin_itemsId)
#     # N = 10
#     # b = [a[i:i + N] for i in range(0, len(a) + 1, N)]
#     # for ls in b:
#     #     get_product_infos(ls)
#     fr.close()
#     ferr.close()
#     tf = datetime.now(pytz.UTC)
#     print str(t), str(tf), str(tf - t)
#     return api_dict


#传入商品页面的html和商品的id
def get_info(html, itemsurl):

    #----
    is_Refurbished = False

    # items_info = {'itemsId':'', 'price':'', 'stock':'','brand':'', 'title':'','reviews':'','Specification':''}

    # items_info = ['itemsId', 'price', 'stock', 'brand', 'title', 'img1', 'img2', 'img3', 'img4',
    #           'img5', 'detail1', 'detail2', 'detail3', 'detail4', 'Specification']
    items_info = []
    # ------------itemsId------------
    itemsId_list = re.findall(r'/dp/(.*?)/ref', itemsurl, re.S)
    itemsId = ''.join(itemsId_list)
    # print itemsId
    items_info.append(str(itemsId))

    #调用api
    result_response = get_product_infos(itemsId,itemsurl)
    print (result_response)

    # print ' ------------Price------------'
    try:
        price = re.findall(r'<span id="priceblock_ourprice" class="a-size-medium a-color-price">(.*?)</span>', html,re.S)[0]
        price = price.split('$')[1].replace('-','')
    except Exception:
        price_detail = result_response['detail']
        last_price = price_detail['ListPrice']
        price = last_price['FormattedPrice']
        price = price.split('$')[1]

    items_info.append(str(price))

    # print '------------Stock------------'
    is_stock = True
    try:
        stock_info_list = re.findall(r'<span class="a-size-medium a-color-success">(.*?)</span>',html,re.S)
        stock_info = re.findall(r'[A-Z].*k',str(stock_info_list),re.S)
        if stock_info:
            stock = stock_info
            is_stock = True
        else:
            stock = 'None'
            is_stock = False
        # items_info['stock'] = stock
    except Exception:
        stock = 'Fail'

    items_info.append(str(stock))

    # print ' ------------brand------------'

    brand = result_response['brand']
    items_info.append(str(brand))

    # print ' ------------title------------'

    title = result_response['title']
    items_info.append(str(title))

    if str(title).find("Refurbished") == -1 or str(title).find("used") ==-1:
        is_Refurbished = False
    else:
        is_Refurbished = True

    # ------------Reviews------------
    # review = ''
    # review_count = re.findall(r'<span id="acrCustomerReviewText" class="a-size-base">(.*?)</span>',html,re.S)
    # print review_count+'======'
    # review = str(review_count).split(' ')[0]
    # items_info['reviews'] = review

    # print ' ------------image------------'
    image_list = result_response['image_list']
    if image_list == []:
        image_list = ['','','','','']
    while len(image_list) < 5:
        image_list.append("")

    # print type(image_list)
    images = image_list[:5]  # 最多取5张图片
    items_info += images

    #------------details------------
    # 前有\xe2\x9c\x94     \xc2\xa0
    details_Feature = result_response['detail']
    details_list = details_Feature['Feature']

    if isinstance(details_list, str):
        details_list = [details_list]
        print (details_list)

    while len(details_list)<4:
        details_list.append("")

    details_list = details_list[:4]
    for i in range(0,4):
        details_list[i] = str(details_list[i]).replace('\n','').replace('\xe2\x9c\x94','').replace('\xc2\xa0','').replace('<br>','.').replace('</br>','')

        if str(details_list[i]).find("Refurbished") == -1 or str(details_list[i]).find("used") == -1:
            is_Refurbished = False
        else:
            is_Refurbished = True

    items_info += details_list

    # ------------Specification------------
    Specification = result_response['description']
    if Specification == None or len(Specification)>5000:
        Specification = '\n'
    if len(Specification)  <5000:
        Specification = Specification[:1000]
    Specification = ''.join(Specification)
    Specification = Specification.replace('\n','').replace('\xe2\x9c\x94','').replace('\xc2\xa0','').replace('<b>','').replace('</b>','').replace('<br>','').replace('</br>','').replace('<br/>','')

    items_info.append(str(Specification))
    if str(Specification).find("Refurbished") == -1 or str(Specification).find("used") == -1:
        is_Refurbished = False
    else:
        is_Refurbished = True

    print ('=====================END===================================')
    print (items_info)

    if choice == 'y':
    #stock为None也写入文件
    # Certified Refurbished
        if is_Refurbished == False:
            result_file.write("\t".join(items_info) + "\n")
        else:
            pass
    else:
        if is_stock:
            if is_Refurbished == False:
                result_file.write("\t".join(items_info) + "\n")
            else:
                pass
        else:    # stock为None不写入文件

            with open(ALL_CONFIG.AMAZON_FAIL_URL_FILE,'aw') as fail_url:
                fail_url.write(itemsurl+'\n')

    print ('=============')
    # f.flush()
    item_file.flush()
    result_file.flush()


#把itemsId页面的html传入get_info函数中，把失败的id重新存一个文件
def handle(itemsurl):
    try:
        #商品详情页
        #获取每一个商品页面的html
        html = get_html.get_amazon_html_proxy(itemsurl)
        # print html
        # 获取每一个商品的asin

        if html:
            #调用get_info函数，传入html
            get_info(html,itemsurl)
        else:
            with open(ALL_CONFIG.AMAZON_FAIL_HTML_FILE, 'aw') as h:
                h.write(itemsurl + '\n')

    except Exception as e:
        # print itemsurl, ":",  e
        with open(ALL_CONFIG.AMAZON_FAIL_URL_FILE,'aw') as fail_url:
            fail_url.write(itemsurl+'\n')
        # with open('./Result/no_except.txt', 'aw') as f:
        #     f.write(itemsurl + '\n')

#把items_last.txt文件中的字段制成表格
def create_titles(filename, titles):
    f = open(filename, "w")
    f.write("\t".join(titles) + "\n")
    #清除内部缓冲区
    f.flush()
    #关闭文件
    f.close()

#去重后的items的id文件
def start(items_file):

    global result_file, lock, titles,fr,ferr,item_file
    titles = ['itemsId', 'price', 'stock', 'brand', 'title', 'img1', 'img2', 'img3', 'img4',
              'img5', 'detail1', 'detail2', 'detail3', 'detail4', 'Specification']
    item_file = open(items_file, 'r')

    #调用函数create_titles
    create_titles(ALL_CONFIG.AMAZON_ITEMS_XLS_FILE, titles)
    result_file = open(ALL_CONFIG.AMAZON_ITEMS_XLS_FILE, 'aw')
    items_list = item_file.readlines()
    #把获取的url依次传入handle
    items = []
    for item in items_list:
        item = item.split('\n')[0]
        items.append(item)
    lock = Lock()
    pool = Pool(10)
    #调用函数把items的url依次传入handle函数中爬虫
    pool.map(handle, items)
    pool.close()
    pool.join()

    item_file.close()
    result_file.close()

if __name__ == "__main__":
    #获取api的response
    to_time = str(datetime.now(pytz.UTC) - timedelta(hours = 2)).split('.')[0].replace(' ','T') + 'Z'
    print ('start:',datetime.now(pytz.UTC))
    from_time = str(datetime.now(pytz.UTC) - timedelta(days = 1)).split('.')[0].replace(' ','T') + 'Z'
    amazon_mws = Amazon_MWS()
    amazon_aws = Amazon_AWS()
    # start_api()
    t = datetime.now(pytz.UTC)

    choice = input('Need None(y/n)?\n')

    start(ALL_CONFIG.AMAZON_URLS_FILE)
