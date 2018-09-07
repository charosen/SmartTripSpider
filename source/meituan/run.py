#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Meituan api spider's main runtime program file. In this file, we instantialize
an instance of MT_spider.
'''

from spider_develop import MeituanSpider


# saveMode ：txt存储为txt文件，csv存储为csv文件，
# mongodb存储在mongo数据库中，neo4j存储在neo4j数据库中，无输入默认为txt

# spider = MeituanSpider(saveMode='txt')
spider = MeituanSpider(saveMode='neo4j')
# spider = MeituanSpider(saveMode='mongodb')
# spider = MeituanSpider(saveMode='csv')

spider.run()
