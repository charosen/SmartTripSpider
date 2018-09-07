#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import jieba
import jieba.analyse

with open('./ctripqainfos/HainanQAinfo.txt') as file:
    data = file.read()
    tag = jieba.analyse.extract_tags(data)
    print(tag)
