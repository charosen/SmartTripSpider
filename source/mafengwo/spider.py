#!/usr/bin/env python3
# -*- coding:utf-8 -*-

'''
Define a BaseSpider class allows you to fetch all resorts infos in
given province.
'''

import os
import re
import json
import time
import random
import datetime

import requests
from lxml import etree
from proxy import SpiderProxy
from requests.exceptions import ProxyError, HTTPError, RequestException, \
                                Timeout, ReadTimeout, TooManyRedirects

from settings import PROXY_PUNISH, USER_AGENTS, TIMEOUT, save_path, file_name
# 全局变量定义


# 类定义：

# 旅游爬虫基类：
class BaseSpider(object):
    # 文档字符串
    '''
    BaseSpider class allows users to fetch all data from different websites.

    :Usage:

    '''
    # 类静态成员定义
    SAVE_MODES = ('json', 'txt')

    # 初始化方法
    def __init__(self, area_name='海南'):
        # 文档字符串
        '''
        Initialize a new instance of the BaseSpider.

        :Args:
         - area_name : a str of Chinese area name which data are located
         in.

        '''
        # 方法实现
        self.area_name = area_name
        self.data = list()

        # 初始化爬虫代理
        # self.proxyer = SpiderProxy()

    # HTTP请求头配置方法
    def config_header(self, host):
        pass

    #  HTTP请求代理配置方法
    def config_proxy(self):
        self.proxy_url = self.proxyer.pop_proxy()
        # print('1> proxy:', self.proxy_url)
        return {
            'http': 'http://' + self.proxy_url,
            'https': 'https://' + self.proxy_url
         }

    # 数据存储方法
    def dump_data(self, save_mode='json'):
        # 文档字符串
        '''
        Dump spider fetched data into a file specified by `save_mode` para.

        :Args:
         - save_mode : file type to save spider fectched data.

        '''
        # 方法实现
        if save_mode not in self.SAVE_MODES:
            raise RuntimeError('存储模式指定有误，请输入txt、json')
        # create json file object:
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        file_path = os.path.join(save_path, file_name+'.'+save_mode)
        with open(file_path, 'w', encoding='utf-8') as file:
            if save_mode == 'json':
                json.dump(self.data, file, ensure_ascii=False)
            elif save_mode == 'txt':
                # 只是初步用于QA问题爬取
                # 对于txt模式存储，还需进一步思考和修改
                for data in self.data:
                    file.write(''.join([data, '\n']))
            else:
                # 此处可以拓展其他文件存储类型
                pass

    # HTTP请求页面方法
    def request_html(self, method, url, **kwargs):
        # 文档字符串
        '''
        Requests website's HTML source code.

        If Timeout, ProxyError, HTTPError, ReadTimeout, TooManyRedirects
        exception occured, retries HTTP Request 10 times; If retry exceeded 10
        times or other exceptions occured, return None.

        :Args:
         - method : method for new HTTP Requests supported by the :class
           `Request` object in `requests` module.
         - url : URL for new HTTP Requests supported by the :class`Request`
           object in `requests` module.
         - **kwargs : key words arguments supported by the :class:`Request`
           object in `requests` module.

        :Returns:
         - html : a :class:`Response` if request suceeded or None if
           exceptions occured.

        '''
        # 方法实现
        # html = None
        error = False
        num = 1
        while True:
            try:
                response = requests.request(method, url,
                                            # proxies=self.config_proxy(),
                                            **kwargs)
                # print(response.encoding)
                response.raise_for_status()
                response.encoding = 'utf-8'
                # html = response
                print('2>> Request Webpage Success.')
            except (Timeout, ProxyError, HTTPError,
                    ReadTimeout, TooManyRedirects) as e:

                print('2>> Exceptions Occured:', e)
                print(f'2>> Retries {num} times.')
                response = None
                # self.proxyer.counter[self.proxy_url] -= PROXY_PUNISH
                num += 1
                if num > 10:
                    print('2>> Exceed maximum retry times.')
                    # 日志记录
                    error = True
            except RequestException as e:
                print('2>> Exception Occured:', e)
                # 日志记录
                response = None
                # self.proxyer.counter[self.proxy_url] -= PROXY_PUNISH
                error = True
            finally:
                if response or error:   # 原来的response是html
                    break
                # timeout retry pause.
                # time.sleep(1)
                # time.sleep(random.randint(1,3))
        return response


# 马蜂窝旅游景点爬虫子类：
class MafengwoSpider(BaseSpider):
    # 文档字符串
    '''
    MafengwoSpider class allows users to fetch all resort data from mafengwo
    websites.

    :Usage:

    '''
    # 类静态成员定义
    base_url = "http://www.mafengwo.cn/search/s.php?t=poi&kt=1"
    location_api = "http://pagelet.mafengwo.cn/poi/pagelet/poiLocationApi"
    # tickets_api = "http://pagelet.mafengwo.cn/poi/pagelet/poiTicketsApi"
    req_host = {"www": "www.mafengwo.cn", "pagelet": "pagelet.mafengwo.cn"}
    key_convert = {
        "交通": "transInfo", "门票": "ticketsInfo", "开放时间": "openInfo",
     }

    # 初始化方法
    def __init__(self, area_name='海南'):
        # 文档字符串
        '''
        Initialize a new instance of the MafengwoSpider.

        :Args:
         - area_name : a str of Chinese area name which data are located
         in.

        '''
        # 方法实现
        super(MafengwoSpider, self).__init__(area_name)
        self.links = list()

    # 爬虫主程序
    def run(self):
        # 文档字符串
        '''
        Main spider method of MafengwoSpider.

        Fetches all resorts links, parses every resort website according to
        their links then packes all dictionary formatted resorts' info data
        into a data list.
        '''
        # error counter variable
        start = time.time()
        num = 1
        # 方法实现
        self.get_links()
        for link in self.links:
            print(f'>>>> getting resorts webpage:', link)
            html = self.request_html('GET', link, timeout=TIMEOUT,
                                     headers=self.config_header('www'))
            # time.sleep(1)
            # time.sleep(random.randint(1,3))
            if html:
                while True:
                    test = etree.HTML(html.text).xpath(
                            '//div[@class="row row-top" '
                            'or @data-anchor="overview"]')
                    if len(test) == 2:
                        print(f'>>>> Success getting resort {link}.')
                        self.data.append(self.parse_resort(html.text))
                        break
                    # 走到这里的时候说明代理ip被禁了，换新ip重新请求一次
                    # 相信代理ip池中一定有可靠ip，因此不会出现死循环
                    self.proxyer.counter[self.proxy_url] -= PROXY_PUNISH
                    print('>>>> getting wrong resort content. Retries again!')
                    html = self.request_html('GET', link, timeout=TIMEOUT,
                                             headers=self.config_header('www'))
            else:
                print(f'>>>> Failure getting resort {link}.')
                # 防止网络不可靠情况下，爬虫一直运行下去：
                if num == 1:
                    num += 1
                    lastLink = self.links.index(link)
                else:
                    if self.links.index(link) != lastLink + 1:
                        num = 1
                    elif num <= 10:
                        num += 1
                        lastLink = self.links.index(link)
                    else:
                        raise ValueError('NetWork Unavailable!')
        print(len(self.links))
        print(len(self.data))
        end = time.time()
        print(end-start)

        self.dump_data('json')
        # print(self.data)
        # print(len(self.links))
        # print(len(self.data))

    # HTTP请求头配置方法
    def config_header(self, host_key):
        # 文档字符串
        '''
        Loads Mafengwo's HTTP Requests Header with random User-Agents.

        :Args:
         - host_key : a str of Host's key.
           www - www.mafengwo.cn; pagelet - pagelet.mafengwo.cn
        :Returns:
         a dict of HTTP Requests Header.
        '''
        # 方法实现
        # 可以使用python第三方库fake-useragent实现随机user-agent
        useragent = random.choice(USER_AGENTS)
        print('> user agent:', useragent)
        return {
            'Accept': ('text/html,application/xhtml+xml,application/xml;'
                       'q=0.9,image/webp,image/apng,*/*;q=0.8'),
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Host': self.req_host[host_key],
            'User-Agent': useragent,
            'Proxy-Connection': 'keep-alive',
        }

    # 获取所有景点链接方法
    def get_links(self, pStart=1, pEnd=50):
        # 文档字符串
        '''
        Fetches all resorts' links on Mafengwo website during given pages.

        Uses xpath to parse fetched websites' HTML and iterates parsed HTML
        elements, then updates the resorts' links container `self.links` if
        element text contains resort type word.

        :Args:
         - pStart : An int of starting website page.
         - pEnd : An int of ending website page.
        '''
        # error counter variable
        num = 1
        # 方法实现
        for page in range(pStart, pEnd+1):
            print(f'>>> Getting page {page}')
            req_param = {'p': page, 'q': self.area_name}
            html = self.request_html('GET', self.base_url,
                                     params=req_param, timeout=TIMEOUT,
                                     # proxies=self.config_proxy(),
                                     headers=self.config_header('www'))
            # time.sleep(random.randint(1,3))
            # time.sleep(1)
            if html:
                while True:
                    selector = etree.HTML(html.text)
                    elements = selector.xpath('//div[@class="att-list"]/ul'
                                              '/li/div/div[2]/h3/a')
                    print('>>> links count:', len(elements))
                    if len(elements) == 15:
                        print(f'>>> Success getting page {page}.')
                        self.links.extend([e.get('href') for e
                                           in elements if '景点' in e.text])
                        break
                    # 走到这里的时候说明代理ip被禁了，换新ip重新请求一次
                    # 相信代理ip池中一定有可靠ip，因此不会出现死循环
                    self.proxyer.counter[self.proxy_url] -= PROXY_PUNISH
                    print('>>> getting wrong page content. Retrise again!')
                    html = self.request_html('GET', self.base_url,
                                             params=req_param, timeout=TIMEOUT,
                                             # proxies=self.config_proxy(),
                                             headers=self.config_header('www'))
            else:
                print(f'>>> Failure getting page {page}.')
                # 防止网络不可靠情况下，爬虫一直运行下去：
                if num == 1:
                    num += 1
                    lastPage = page
                else:
                    if page != lastPage + 1:
                        num = 1
                    elif num <= 10:
                        num += 1
                        lastPage = page
                    else:
                        raise ValueError('NetWork Unavailable!')
        # print(self.links)

    # 解析景点数据方法
    def parse_resort(self, html):
        # 文档字符串
        '''
        Parses given resort's info data, pack them into a dictionary and return
        dictionary formatted data.

        :Args:
         - html : a str of html source code of given resort.

        :Returns:
         - item : a dict of parsed resort's info data.
        '''
        # 方法实现
        print('>>> start parsing resort.')
        item = {
            'resortName': None,
            'poi_id': None,
            'introduction': None,
            'areaName': None,
            'areaId': None,
            'address': None,
            'lat': None,
            'lng': None,
            'openInfo': None,
            'ticketsInfo': None,
            'transInfo': None,
            'tel': None,
            'item_site': None,
            'item_time': None,
            'payAbstracts': None,
            # administrative field:
            'source': 'mafengwo',
            'timeStamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }

        row_top, overview = etree.HTML(html).xpath(
                                    '//div[@class="row row-top" '
                                    'or @data-anchor="overview"]')

        mod_detail = overview.xpath('//div[@class="mod mod-detail"]')
        if len(mod_detail) == 1:
            for dl in mod_detail[0].xpath('dl'):
                dt, dd = dl
                # transform keys and insert key-value pair into dict.
                item[self.key_convert.get(dt.text)] = dd.xpath(
                                                          'string()').strip()

            intro = mod_detail[0].xpath('div[@class="summary"]')
            if len(intro) == 1:
                item['introduction'] = intro[0].xpath('string()').strip()

            base_info = mod_detail[0].xpath('ul[@class="baseinfo clearfix"]')
            if len(base_info) == 1:
                for li in base_info[0].xpath('li'):
                    # print(li.get('class'))
                    content = li.xpath('div[@class="content"]').pop()
                    item[li.get('class').replace('-', '_')] = content.xpath(
                                                            'string()').strip()
        # 后面可以改改
        a = row_top.xpath('//div[@class="drop"]/span/a').pop()
        item['resortName'] = row_top.xpath('//div[@class="title"]'
                                           '/h1/text()').pop()
        item['areaName'] = a.text
        item['areaId'] = int(re.search('(\d+)\.html', a.get('href'))[1])

        mod_location = overview.xpath('div[@class="mod mod-location"]').pop()
        poi = mod_location.xpath(('//div[contains(@data-api,"poiLocationApi")'
                                  ']/@data-params')).pop()
        while True:
            try:
                response = self.request_html('GET', self.location_api,
                                             params={'params': poi},
                                             timeout=TIMEOUT,
                                             # proxies=self.config_proxy(),
                                             headers=self.config_header(
                                                                   'pagelet'))
                apiData = response.json()['data']
            except:
                print('>> acquired location fail! Retries Again.')
            else:
                break
        item['address'] = mod_location.xpath('//p[@class="sub"]/text()').pop()
        item['poi_id'] = int(json.loads(poi)['poi_id'])
        item['lat'] = apiData['controller_data']['poi']['lat']
        item['lng'] = apiData['controller_data']['poi']['lng']

        print('>>> end parsing resort.')
        return item


# 携程旅游酒店爬虫子类
class CtripSpider(BaseSpider):
    # 文档字符串
    '''
    CtripSpider class allows users to fetch all hotel data from ctrip websites.

    :Usage:

    '''
    # 类静态成员定义
    base_url = "https://hotels.ctrip.com/hotel/{}"

    # 初始化方法
    def __init__(self, area_name="sanya43"):
        # 文档字符串
        '''
        Initialize a new instance of the CtripSpider.

        :Args:
         - area_name : a str of Chinese area name which data are located
         in.

        '''
        # 方法实现
        # 设想：先翻译成英文-sanya，然后请求城市id-43
        super(CtripSpider, self).__init__(area_name)
        self.page_url = self.base_url.format(self.area_name)
        # print('1> page_url =', self.page_url)

    # 爬虫主程序
    def run(self):
        # 文档字符串

        # 方法实现
        # 准备请求参数
        num = 1
        start = time.time()
        for page in range(1, self.get_page_num()):
            # print(f'4>>>> parsing hotels list page {page}')
            elements = None
            html = self.request_html('GET',
                                     '/'.join([self.page_url, f'p{page}']),
                                     headers=self.config_header(),
                                     timeout=TIMEOUT)
            if html:
                while True:
                    selector = etree.HTML(html.text)
                    elements = selector.xpath("//div[contains(@class"
                                              ",'hotel_new_list')]")
                    if len(elements):
                        # print(f'4>>>> Success parsing hotel list page{page}')
                        break
                    # 走到这里的时候说明代理ip被禁了，换新ip重新请求一次
                    # 相信代理ip池中一定有可靠ip，因此不会出现死循环
                    # self.proxyer.counter[self.proxy_url] -= PROXY_PUNISH
                    print('4>>>> getting wrong page content. Retrise again!')
                    html = self.request_html('GET',
                                             '/'.join(self.page_url,
                                                      f'p{page}'),
                                             timeout=TIMEOUT,
                                             headers=self.config_header())
                for elem in elements:
                    self.data.append(self.parse_hotel(elem))
            else:
                print(f'4>>>> Failure getting page {page}.')
                # 防止网络不可靠情况下，爬虫一直运行下去：
                if num == 1:
                    num += 1
                    lastPage = page
                else:
                    if page != lastPage + 1:
                        num = 1
                    elif num <= 10:
                        num += 1
                        lastPage = page
                    else:
                        raise ValueError('NetWork Unavailable!')

        print(len(self.data))
        end = time.time()
        print(end-start)
        self.dump_data('json')

    # HTTP请求头配置方法
    def config_header(self):
        # 文档字符串
        '''
        Loads Ctrip's HTTP Requests Header with random User-Agents.

        :Args:

        :Returns:
         - a dict of HTTP Requests Header.
        '''
        # 方法实现
        # 可以使用python第三方库fake-useragent实现随机user-agent
        useragent = random.choice(USER_AGENTS)
        # print('1> user agent:', useragent)
        return {
            'Authority': 'hotels.ctrip.com',
            'Accept': ('text/html,application/xhtml+xml,application/xml;'
                       'q=0.9,image/webp,image/apng,*/*;q=0.8'),
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'max-age=0',
            'User-Agent': useragent,
        }

    # 获取未来n天日期的方法
    def get_recent_date(self, n):
        # 文档字符串
        '''
        Returns future n day's date from today.

        :Arg:
         - n : an int of day number.

        :Returns:
         - a str of future n day's date.
        '''
        # 方法实现
        today = datetime.date.today()
        delta_day = datetime.timedelta(days=n)
        return str(today+delta_day)

    # 获取酒店页面数方法
    def get_page_num(self):
        # 文档字符串
        '''
        Get Ctrip's total hotel page number of given area_name.

        :Returns:
         - page_num : an int of Ctrip's total hotel page number.
        '''
        # 方法实现
        # print('2>> Getting page num.')
        html = None
        page_str = None
        while not (html and page_str):
            html = self.request_html('GET', self.page_url, timeout=TIMEOUT,
                                     headers=self.config_header())
            if html:
                selector = etree.HTML(html.text)
                page_str = selector.xpath("string(//div[@class='page_box']"
                                          "//a[@rel='nofollow'])")
        # print('2>> Success getting page num.')
        return int(page_str)

    # 获取酒店数据方法
    def parse_hotel(self, elem):
        # 文档字符串
        '''

        Parses hotel's infos from ctrip's websites.

        Parses hotel's brief infos in ctrips' hotels list page, then jump into
        hotel's detail page and parse its detail infos.

        :Args:
         -elem : a lxml element class of a hotel in Ctrip's website.
        :Returns:
         - item :
        '''
        # 方法实现
        # print('3>>> start parsing hotel.')
        item = {
            'hotel_id': int(elem.xpath("@id").pop()),
            'hotel_name': elem.xpath(".//h2[@class='hotel_name'"
                                     "]/a/@title").pop(),
            'address': elem.xpath((".//p[@class='hotel_item_htladdress"
                                   "']/text()")).pop().strip('】 '),
            'business_zone': elem.xpath((".//p[@class='hotel_item_htladdress"
                                         "']/a[1]/text()")).pop(),
            'lowest_price': int(elem.xpath(("string(.//div[contains(@class,"
                                            "'hotel_price')]/a)"))),
            'hotel_label': list(),
            'newbooking': None,
            'hotel_level': None,
            'hotel_score': 0,
            'hotel_proposition': 0,
            'judge_count': 0,
            'recommend': None,
            'ctrip_qualified': False,
            'ctrip_star': 0,
            'country_star': 0,
            'ctrip_corporate': None,
            'sale_amount': 0,
            'reserve_count': 0
        }
        ico, label, judge = elem.xpath(".//span[@class='hotel_ico']"
                                       "|.//span[@class='special_label']"
                                       "|.//div[@class='hotelitem_judge_box']")
        # print(etree.tostring(ico, encoding='utf-8').decode('utf-8'))
        # 更新携程质量担保字段
        if len(ico.xpath('./span[@class="ico_quality_gold"]')) == 1:
            # print('a')
            item['ctrip_qualified'] = True
        # 更新携程合作等级字段
        corporate = ico.xpath('./span[@data-role="title"]')
        if len(corporate) == 1:
            item['ctrip_corporate'] = corporate.pop().get("class")
        # 更新携程酒店星级字段
        ctrip_star = ico.xpath("./span[contains(@class,'hotel_diamond')]"
                               "/@class")
        if len(ctrip_star) == 1:
            item['ctrip_star'] = int(ctrip_star[0].strip('hotel_diamond'))
        # 更新国家酒店星级字段
        country_star = ico.xpath("./span[contains(@class,'hotel_stars')]"
                                 "/@class")
        if len(country_star) == 1:
            item['country_star'] = int(country_star[0].strip('hotel_stars'))
        # 更新酒店标签字段
        item['hotel_label'].extend(label.xpath('.//text()'))
        # 更新酒店评价等级字段
        hotel_level = judge.xpath('string(.//span[@class="hotel_level"])')
        if len(hotel_level) > 0:
            item['hotel_level'] = hotel_level
        # 更新酒店评分字段
        hotel_score = judge.xpath('string(.//span[@class="hotel_value"])')
        if len(hotel_score) > 0:
            item['hotel_score'] = float(hotel_score)
        # 更新酒店推荐率字段
        hotel_propo = judge.xpath('string(.//span[@class='
                                  '"total_judgement_score"]/span)')
        if len(hotel_propo) > 0:
            item['hotel_proposition'] = int(hotel_propo.strip('%')) / 100
        # 更新酒店评价人数字段
        judge_count = judge.xpath('string(.//span[@class='
                                  '"hotel_judgement"]/span)')
        if len(judge_count) > 0:
            item['judge_count'] = int(judge_count)
            item['sale_amount'] = item['lowest_price'] * item['judge_count']
            item['reserve_count'] = (item['hotel_proposition']
                                     * item['judge_count'])
        # 更新酒店总评字段
        recommend = judge.xpath('string(.//span[@class="recommend"])')
        if len(recommend) > 0:
            item['recommend'] = recommend
        # 更新最新预订字段
        newbook = elem.xpath('string(.//p[@class="hotel_item_last_book"])')
        if len(newbook) > 0:
            item['newbooking'] = newbook

        # 准备酒店url
        hotel_url = self.base_url.format(f"{str(item['hotel_id'])}.html")
        # print(hotel_url)
        # print(f'3>>> end parsing hotel {item["hotel_id"]}.')

        item.update(self.parse_hotel_detail(hotel_url))
        return item

    # 解析酒店详情数据方法
    def parse_hotel_detail(self, url):
        # 文档字符串
        '''
        Parses hotel details data of Ctrip website.

        :Args:
         - url : a str of specified hotel's detail website.
        :Returns:
         - a dict of completary key-value pairs extract from hotel's detail
           info.

        '''
        # 方法实现
        item = {
            "contact": None,
            "introduction": None,
            "hotel_facilities": dict(),
            "hotel_policy": dict(),
            "surround_facilities": dict()
        }
        params = dict(isFull='F', checkin=self.get_recent_date(1),
                      checkout=self.get_recent_date(2))
        # print('2> params:', params)
        # print('3>>> getting hotel detail:', url)
        hotel_info = None
        html = self.request_html('GET', url, timeout=TIMEOUT, params=params,
                                 headers=self.config_header())
        if html:
            while True:
                hotel_info = etree.HTML(html.text).xpath('//div[@id="hotel_'
                                                         'info_comment"]')
                if len(hotel_info) == 1:
                    # print('3>>> success getting detail:', url)
                    break
                # 走到这里的时候说明代理ip被禁了，换新ip重新请求一次
                # 相信代理ip池中一定有可靠ip，因此不会出现死循环
                # self.proxyer.counter[self.proxy_url] -= PROXY_PUNISH
                print('3>>> getting wrong hotel detail. Retries again!')
                html = self.request_html('GET', url,
                                         timeout=TIMEOUT, params=params,
                                         headers=self.config_header())

            # 解析详情
            hotel_intro = hotel_info[0].xpath('.//div[@id="htlDes"]')
            if len(hotel_intro) == 1:
                phone = hotel_intro[0].xpath('string(.//span[@data-real]'
                                             '/@data-real)')
                if len(phone) > 0:
                    pattern = '(\(\d{3,4}\)|\d{3,4}-|\s)?\d{8}'
                    item.update(contact=re.search(pattern,
                                                  phone.strip()).group(0))
                intro = hotel_intro[0].xpath('string(.//span[@itemprop='
                                             '"description"])')
                if len(intro) > 0:
                    item.update(introduction=intro.strip())
            hotel_facility = hotel_info[0].xpath(".//div[@id="
                                                 "'J_htl_facilities']")
            if len(hotel_facility) == 1:
                for tr in hotel_facility[0].xpath('.//tr[@data-init]'):
                    key = tr.xpath('string(./th)')
                    value = tr.xpath('.//li[@title]/@title')
                    item['hotel_facilities'].setdefault(key, value)
            hotel_policy = hotel_info[0].xpath('.//h2[text()="酒店政策"]')
            if len(hotel_policy) == 1:
                for tr in hotel_policy[0].getnext().xpath('.//tr'):
                    key = tr.xpath('string(./th)')
                    if key == "儿童政策" or "可用支付方式":
                        continue
                    value = tr.xpath('string(./td)')
                    item['hotel_policy'].setdefault(key, value)
            surround = hotel_info[0].xpath('.//h2[text()="周边设施"]')
            if len(surround) == 1:
                for tr in surround[0].getnext().xpath('.//tr'):
                    key = tr.xpath('string(./th)')
                    value = tr.xpath('.//li/text()')
                    item['surround_facilities'].setdefault(key, value)

        else:
            print(f'3>>> Failure getting hotel {url}.')

        # print(item)
        return item


# 马蜂窝旅游问答爬虫子类
class MafengwoQASpider(BaseSpider):
    # 文档字符串
    '''
    MafengwoQASpider class allows users to fetch all questions from mafengwo
    websites.

    :Usage:

    '''
    # 类静态成员定义
    accept_dict = {
        'normal': ('text/html,application/xhtml+xml,application'
                   '/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
        'ajax': 'application/json, text/javascript, */*; q=0.01'
    }
    base_url = 'http://www.mafengwo.cn/wenda'
    ajax_url = 'http://www.mafengwo.cn/qa/ajax_qa/more'

    # 初始化方法
    def __init__(self, area_name='area-12938'):
        # 文档字符串
        '''
        Initialize a new instance of the MafengwoQASpider.

        :Args:
         - area_name : a str of Chinese area name which data are located
         in.

        '''
        # 方法实现
        super(MafengwoQASpider, self).__init__(area_name)
        self.area_id = int(self.area_name.strip('area-'))
        print(self.area_id)

    # 爬虫主程序
    def run(self, ):
        # 文档字符串

        # 方法实现
        # 没加入差错控制机制，待更新
        url = '/'.join([self.base_url, f'{self.area_name}.html'])
        params = {'type': 3, 'mddid': self.area_id, 'sort': 8,
                  'tid': '', 'time': '', 'key': ''}
        response = self.request_html('GET', url, timeout=TIMEOUT,
                                     headers=self.config_header('normal'))
        self.data.extend(self.parse_question(response.text))
        for page in range(self.get_page_num()):
            print(f'>> parsing {page} questions.')
            params.update(page=page)
            response = self.request_html('GET', self.ajax_url,
                                         timeout=TIMEOUT, params=params,
                                         headers=self.config_header('ajax'))
            if response.json().get('data'):
                html = response.json()['data'].get('html')
                if html:
                    self.data.extend(self.parse_question(html))
        print(len(self.data))
        self.dump_data(save_mode='txt')

    # HTTP请求头配置方法
    def config_header(self, req_type):
        # 文档字符串
        '''
        Loads MafegnwoQA's HTTP Requests Header with random User-Agents.

        :Args:
         - req_type : a str of request type `normal` or `ajax`.
        :Returns:
         - a dict of HTTP Requests Header.
        '''
        # 方法实现
        # 可以使用python第三方库fake-useragent实现随机user-agent
        useragent = random.choice(USER_AGENTS)
        print('1> user agent:', useragent)
        header = {
            'Accept': self.accept_dict[req_type],
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Host': 'www.mafengwo.cn',
            'Proxy-Connection': 'keep-alive',
            'User-Agent': useragent
        }
        if req_type == 'normal':
            header.update({'Cache-Control': 'max-age=0'})

        return header

    # 获取问答异步加载页面数方法
    def get_page_num(self):
        # 文档字符串
        '''
        Get mafengwo's total question page number of given area_name.

        :Returns:
         - page_num : an int of mafengwo's total question page number.

        '''
        # 方法实现
        # 参数准备
        print('2>> Getting page num.')
        params = {'type': 3, 'mddid': self.area_id, 'sort': 8, 'page': 1,
                  'tid': '', 'time': '', 'key': ''}
        response = None
        total_num = None
        while not (response and total_num):
            response = self.request_html('GET', self.ajax_url,
                                         params=params, timeout=TIMEOUT,
                                         headers=self.config_header('ajax'))
            if response:
                if response.json().get('data'):
                    total_num = response.json()['data'].get('total')
        print('2>> Success getting page num.')
        # 一次加载有20个数据
        return (total_num//20)+1

    # 解析问答数据方法
    def parse_question(self, html):
        # 文档字符串
        '''
        Parses given question page's info data, pack them into a list and
        return them.

        :Args:
         - html : a str of html source code of given question page.

        :Returns:
         - a list of parsed question's info data.
        '''
        # 方法实现
        return etree.HTML(html).xpath('//li[contains(@class, "item clearfix")]'
                                      '/div[@class="title"]/a/text()')


class BaiduPoiSpider(BaseSpider):
    # 文档字符串
    '''
    BaiduPoiSpider class allows users to fetch all kinds of poi data provided
    by Baidu API.

    :Usage:

    '''
    # 类静态成员定义
    city_coord = {
        "海口": [(19.926987, 110.157237), (20.145149, 110.572326)],
    }
    LEGAL_TAGS = ["美食", "中餐厅", "外国餐厅", "小吃快餐店", "蛋糕甜品店", "咖啡厅",
            "茶座", "酒吧", "酒店", "星级酒店", "快捷酒店", "公寓式酒店", "购物",
            "购物中心", "百货商场", "超市", "便利店", "家居建材", "家电数码", "商铺",
            "集市", "生活服务", "通讯营业厅", "邮局", "物流公司", "售票处", "洗衣店",
            "图文快印店", "照相馆", "房产中介机构", "公用事业", "维修点", "家政服务",
            "殡葬服务", "彩票销售点", "宠物服务", "报刊亭", "公共厕所", "丽人", "美容",
            "美发", "美甲", "美体", "旅游景点", "公园", "动物园", "植物园", "游乐园",
            "博物馆", "水族馆", "海滨浴场", "文物古迹", "教堂", "风景区", "休闲娱乐",
            "度假村", "农家院", "电影院", "KTV", "剧院", "歌舞厅", "网吧", "游戏场所",
            "洗浴按摩", "休闲广场", "运动健身", "体育场馆", "极限运动场所", "健身中心",
            "教育培训", "高等院校", "中学", "小学", "幼儿园", "成人教育", "亲子教育",
            "特殊教育学校", "留学中介机构", "科研机构", "培训机构", "图书馆", "科技馆",
            "文化传媒", "新闻出版", "广播电视", "艺术团体", "美术馆", "展览馆",
            "文化宫", "医疗", "综合医院", "专科医院", "诊所", "药店", "体检机构",
            "疗养院", "急救中心", "疾控中心", "汽车服务", "汽车销售", "汽车维修",
            "汽车美容", "汽车配件", "汽车租赁", "汽车检测场", "交通设施", "飞机场",
            "火车站", "地铁站", "地铁线路", "长途汽车站", "公交车站", "公交线路",
            "港口", "停车场", "加油加气站", "服务区", "收费站", "桥", "充电站",
            "路侧停车位", "金融", "银行", "ATM", "信用社", "投资理财", "典当行",
            "房地产", "写字楼", "住宅区", "宿舍", "公司企业", "公司", "园区", "农林园艺",
            "厂矿", "政府机构", "中央机构", "各级政府", "行政单位", "公检法机构",
            "涉外机构", "党派团体", "福利机构", "政治教育机构", "出入口", "高速公路出口",
            "高速公路入口", "机场出口", "机场入口", "车站出口", "车站入口", "门",
            "停车场出入口", "自然地物", "岛屿", "山峰", "水系"]

    base_url = ("http://api.map.baidu.com/place/v2/search?"
                "output=json&page_size=20&scope=2")

    # 初始化方法
    def __init__(self, baidu_ak, area_name="海口", tag="交通设施"):
        # 文档字符串
        '''
        Initialize a new instance of the BaiduPoiSpider.

        :Args:
         - baidu_ak : an str of ak of Baidu Web Place API.
         - area_name : a str of Chinese area name which data are located in.
         - tag : a str of type tag of baidu poi data. Please refer to Baidu API
         WebSite for all defined type tags.

        '''
        # 方法实现
        if tag not in self.LEGAL_TAGS:
            raise RuntimeError('请求类型TAG指定有误，请输入合法类型TAG')
        super(BaiduPoiSpider, self).__init__(area_name)
        self.tag = tag
        self.ak = baidu_ak

    # HTTP请求头配置方法
    def config_header(self):
        # 文档字符串
        '''
        Loads BaiduPoiSpider's HTTP Requests Header with random User-Agents.

        :Returns:
         - a dict of HTTP Requests Header.
        '''
        # 方法实现
        # 可以使用python第三方库fake-useragent实现随机user-agent
        useragent = random.choice(USER_AGENTS)
        print('1> user agent:', useragent)
        return {
            'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                       'image/webp,image/apng,*/*;q=0.8'),
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Host': 'api.map.baidu.com',
            'Proxy-Connection': 'keep-alive',
            'User-Agent': random.choice(USER_AGENTS)
        }

    # 划分坐标矩形方法
    def coord_div(self, delta):
        # 文档字符串
        '''
        Divide city coordinates rectangle into multiple small coordinates
        rectangles, and pack southwest coordiante and northeast coordinate
        into a list.

        :Args:
         - delta : a float of length of small rectangle.
        '''
        # 方法实现
        coord_sw, coord_ne = self.city_coord[self.area_name]
        print(coord_sw, coord_ne)
        lat_count = int((coord_ne[0]-coord_sw[0])/delta + 1)
        lng_count = int((coord_ne[1]-coord_sw[1])/delta + 1)
        print(lat_count, lng_count)

        self.coord_list = list()

        for i in range(0, lat_count):
            lat = coord_sw[0] + delta*i
            for j in range(0, lng_count):
                lng = coord_sw[1] + delta*j
                small_rect = ','.join([str(lat), str(lng), str(lat+delta), str(lng+delta)])
                self.coord_list.append(small_rect)

        print(self.coord_list)

    # 爬虫主程序
    def run(self, ):
        # 文档字符串
        '''
        Main spider method of BaiduPoiSpider.


        '''
        self.coord_div(0.03)

        for bound in self.coord_list:
            print('>> start fetching:', bound)
            num = 1
            for page in range(0, self.get_page_num(bound)):
                print(f'>> {bound} request page {page}')
                para = {"bounds": bound, "ak": self.ak,
                        "page_num": page, "query": self.tag}
                response = self.request_html("GET", self.base_url,
                                             params=para,
                                             timeout=TIMEOUT,
                                             headers=self.config_header())
                time.sleep(1)
                if response:
                    if response.json()['status'] != 0:
                        raise RuntimeError(response.json()['message'])
                    self.data.extend(response.json()['results'])

                else:
                    print(f'>>> Failure getting page {page}.')
                    # 防止网络不可靠情况下，爬虫一直运行下去：
                    if num == 1:
                        num += 1
                        lastPage = page
                    else:
                        if page != lastPage + 1:
                            num = 1
                        elif num <= 10:
                            num += 1
                            lastPage = page
                        else:
                            raise ValueError('NetWork Unavailable!')
            print('>> end fetching:', bound)

        print(self.data, len(self.data))
        self.dump_data()

    def get_page_num(self, bound):
        # 文档字符串
        '''
        Get total page number of Baidu Poi given bound para.

        :Returns:
         - page_num : an int of Baidu POI Response total page num.
        '''
        # 方法实现
        print('2>> Getting page num.')
        para = {"bounds": bound, "ak": self.ak,
                "page_num": 0, "query": self.tag}
        response = self.request_html("GET", self.base_url,
                                     params=para, timeout=TIMEOUT,
                                     headers=self.config_header())

        if not response:
            raise RuntimeError("Request Error!")
        elif response.json()['status'] != 0:
            raise RuntimeError(response.json()['message'])

        print('>> Success getting page num.')
        return (response.json()['total']//20) + 1


if __name__ == '__main__':
    ak = "XGdhWf1K4iAPGjSrcLA81TsWb2OuUFn0"
    spider = BaiduPoiSpider(ak)
    spider.run()
