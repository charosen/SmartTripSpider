#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 模块文档字符串
'''
Define a CtripSpider class allows you to fetch ctrip qa infos about Hainan
Province.
'''

# 导入模块
import os
import requests
from lxml import etree
from requests.exceptions import Timeout, ProxyError, HTTPError, RequestException, ReadTimeout, TooManyRedirects

# 全局变量定义
HEADER = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67'
                        '.0.3396.99 Safari/537.36'}
# 数据存储路径和文件名
savePath = './ctripqainfos'
filename = 'HainanQAinfo.txt'


class CtripQASpider:
    # 文档字符串


    # 爬虫静态成员定义
    base_url = "http://you.ctrip.com/asks/search/p{}"

    # 初始化方法
    def __init__(self, *, kw='海南'):
        self.questions = list()
        self.keyword = kw
        if not os.path.exists(savePath):
            os.makedirs(savePath)
        filePath = os.path.join(savePath, filename)
        self.file = open(filePath, 'w', encoding='utf-8')


    # 爬虫主程序
    def run(self, pStart=1, pEnd=50):
        for page in range(pStart, pEnd+1):
            html = self.html_downloader(page)
            if html:
                self.html_parser(html)
        self.data_saver()


    # HTTP请求页面方法
    def html_downloader(self, num):
        try:
            response = requests.get(self.base_url.format(num),
                                    params={'keywords': self.keyword},
                                    headers=HEADER)
            html = response.text
            print('>> Request Webpage Success.')
        except:
            print('>> Exceptions occured!')
            html = None
        finally:
            return html

    # 页面解析方法
    def html_parser(self, html):
        selector = etree.HTML(html)
        for question in selector.xpath('//ul[@class="asklist"]/li/p'):
            self.questions.append(question.xpath('string(.)').strip())

    # 数据存储方法
    def data_saver(self):
        for question in self.questions:
            self.file.write(question + '\n')


    # 析构方法
    def __del__(self):
        self.file.close()


# 测试代码：
if __name__ == '__main__':
    spider = CtripQASpider()
    spider.run()
