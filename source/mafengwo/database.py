#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# 模块字符串：
'''
Defines a Data Saver classes allow users to save all resorts infos data fetched
from different website.
'''


# 导入模块：
# 标准库导入
import json
import os

# 相关第三方库导入
import pymysql
from pymongo import MongoClient as Client
from py2neo import Node, Relationship, Graph

# 本地库导入
from settings import NEO_CONF, MONGO_CONF, SQL_CONF, save_path


# 全局变量：
# 景点数据建表SQL语句
RESORT_SQL = '''CREATE TABLE IF NOT EXISTS {0}(
    poi_id INTEGER NOT NULL,
    resortName VARCHAR(60),
    areaName   VARCHAR(30),
    areaId     INTEGER NOT NULL,
    address    VARCHAR(128),
    lat        FLOAT,
    lng        FLOAT,
    introduction TEXT,
    openInfo   VARCHAR(255),
    ticketsInfo VARCHAR(512),
    transInfo  TEXT,
    tel        VARCHAR(128),
    item_site  VARCHAR(128),
    item_time  VARCHAR(128),
    payAbstracts TEXT,
    source     VARCHAR(30),
    timeStamp  VARCHAR(30)
    );'''
# 酒店数据建表SQL语句
# 酒店数据的结构还需修改，酒店数据还不能操作MySQL数据库
HOTEL_SQL = '''



'''
# 饭店数据建表SQL语句
RESTAURANT_SQL = '''


'''


# 类定义：

# 数据存储器基类
class BaseSaver(object):
    # 文档字符串
    '''
    BaseSaver class allows users to save all infos data fetched from website.

    :Usage:

    '''
    # 数据存储器的静态成员定义
    SAVE_MODES = ('mongodb', 'neo4j', 'mysql')

    # 初始化方法：
    def __init__(self, save_mode="neo4j"):
        # 文档字符串
        '''
        Initialize an instance of BaseSaver.

        :Args:
         - save_mode : a str of database to save data in.
         - create_sql : a str of table creating sql statement for MySQL
           database.

        '''
        # 方法实现
        if save_mode not in self.SAVE_MODES:
            raise RuntimeError('存储模式指定有误，请输入mongodb、neo4j或者mysql')
        self.save_mode = save_mode
        if self.save_mode == 'mongodb':
            # mongodb initialize
            print('>>>> we are in mongodb.')
            self.connector = Client(**MONGO_CONF)[MONGO_CONF.get('authSource')]
        elif self.save_mode == 'neo4j':
            # neo4j initialize
            print('>>>> we are in neo4j.')
            self.connector = Graph(**NEO_CONF)
        else:
            # mysql initialize
            print('>>>> we are in mysql.')
            self.connector = pymysql.connect(**SQL_CONF)

            # 基类不能用来存储数据进入MySQL数据库（未定义下述，报错）
            # Neo4j数据库同理（什么也没做）
            # self.create_sql = RESORT_SQL

    # 数据存储方法：
    def data_save(self, *file_name_iter):
        # 文档字符串
        '''
        Saves spider fetched data into different databases.
        Wipes out the old data and saves the new fetched ones.

        :Args:
         - *file_name_iter : a var-positional params of file name to fetch data
         from and table/collection name to save data in.
        '''
        # 方法实现
        # 此处可以拓展成任意文件类型，其他文件类型的数据转换成json再写即可
        self.json_data = list()
        for file_name in file_name_iter:
            file_path = os.path.join(save_path, file_name+'.json')
            if not os.access(file_path, os.F_OK):
                raise RuntimeError(f'数据文件{file_path}不存在，请检查数据！')
            with open(file_path, 'r', encoding='utf-8') as file:
                self.json_data.extend(json.load(file, encoding='utf-8'))

        if self.save_mode == 'mongodb':
            print('>>> we are saving to mongodb.')
            # 删除原始数据
            self.connector.drop_collection(file_name)
            # 保存新数据
            self.connector[file_name].insert_many(self.json_data)
        elif self.save_mode == 'neo4j':
            print('>>> we are saving to neo4j.')
            # 删除原始数据, 一定要小心使用
            self.graph_cleaner()
            # 保存新数据
            self.graph_builder()
        else:
            print('>>> we are saving to mysql.')
            # 准备sql语句
            data_key = self.json_data[0].keys()
            sql_key = ','.join(data_key)
            sql_value = ', '.join([f'%({key})s' for key in data_key])
            sql = '''
            INSERT INTO {0}({1})
            VALUES ({2});
            '''.format(file_name, sql_key, sql_value)
            print(sql)

            with self.connector.cursor() as cursor:
                cursor.execute(self.create_sql.format(file_name))
                self.connector.commit()
                # 删除原始数据，一定要小心使用
                cursor.execute(f"DELETE FROM {file_name}")
                # 保存新数据
                cursor.executemany(sql, self.json_data)
                self.connector.commit()

    # 知识图谱删除方法：
    def graph_cleaner(self):
        pass

    # 知识图谱生成方法：
    def graph_builder(self):
        pass

    # 数据存储器退出方法：
    def __del__(self):
        # 文档字符串
        '''
        The deconstructor of BaseSaver class.

        Deconstructs an instance of BaseSaver, closes Databases.
        '''
        # 方法实现
        print(f'>>>> closing {self.save_mode}.')
        if self.save_mode == 'mongodb':
            self.connector.client.close()
        elif self.save_mode == 'mysql':
            self.connector.close()


# 马蜂窝景点数据存储器子类：
class MafengwoSaver(BaseSaver):
    # 文档字符串
    '''
    Defines a MafengwoSaver class inherited from BaseSaver class.

    MafengwoSaver class allows users to save all resorts infos data fetched
    from mafengwo website.

    :Usage:

    '''
    # 数据存储器静态成员定义

    # 初始化方法
    def __init__(self, save_mode="neo4j"):
        super(MafengwoSaver, self).__init__(save_mode)
        if self.save_mode == "mysql":
            self.create_sql = RESORT_SQL

    # 知识图谱删除方法
    def graph_cleaner(self):
        # 文档字符串
        '''
        Breaks down knowledge graph of mafengwo resorts data in Graph Database
        Neo4j.

        Detachs isLocateOf relationship, then deletes locate nodes and resort
        nodes.
        '''
        self.connector.run("match (n:locate)-[]-(m:resort) detach delete n, m")

    # 知识图谱生成方法
    def graph_builder(self):
        # 文档字符串
        '''
        Builds a knowledge graph of mafengwo resorts data in Graph Database
        Neo4j.

        Creates locate nodes and resort nodes, then creates isLocateOf
        relationship between them.
        '''
        # 方法实现
        for info in self.json_data:
            print('>> saving:', info)
            areaInfo = {
                'address': info['address'], 'areaId': info['areaId'],
                'areaName': info['areaName'], 'lat': info['lat'],
                'lng': info['lng'], 'source': info['source'],
                'timeStamp': info['timeStamp']
            }
            areaNode = Node("locate", **areaInfo)
            resortNode = Node("resort", **info)
            self.connector.create(areaNode | resortNode)
            self.connector.merge(Relationship(areaNode, 'isLocateOf',
                                              resortNode))


# 携程酒店数据存储器子类
class CtripSaver(BaseSaver):
    # 文档字符串
    '''
    Defines a CtripSaver class inherited from BaseSaver class.

    CtripSaver class allows users to save all hotels infos data fetched from
    ctrip website.

    :Usage:

    '''

    # 类静态成员定义

    # 初始化方法
    def __init__(self, save_mode="neo4j"):
        super(CtripSaver, self).__init__(save_mode)
        if self.save_mode == "mysql":
            self.create_sql = HOTEL_SQL

    # 知识图谱删除方法
    def graph_cleaner(self):
        # 文档字符串
        '''
        Breaks down knowledge graph of ctrip hotels data in Graph Database
        Neo4j.

        Detachs isLocateOf, hasFacilities, hasPolicy, hasSurround relationship,
        then deletes located nodes and hotel nodes and so on.
        '''
        # 方法实现
        self.connector.run("match (n)-[]-(m:hotel) detach delete n, m")

    # 知识图谱生成方法
    def graph_builder(self):
        # 文档字符串
        '''
        Builds a knowledge graph of ctrip hotels data in Graph Database Neo4j.

        Creates located nodes, hotel nodes, facility nodes, policy nodes,
        surround nodes, then creates isLocateOf, hasFacilities, hasPolicy,
        hasSurround relationship between them.
        '''
        # 方法实现
        for info in self.json_data:
            print('>> saving:', info)
            # 准备地点节点属性
            area_info = {
                'address': info['address'],
                'business_zone': info['business_zone']
            }
            # 准备酒店设备节点属性
            facilities_info = info.pop('hotel_facilities')
            # 准备酒店政策节点属性
            policy_info = info.pop('hotel_policy')
            # 准备酒店周边设施节点属性
            surround_info = info.pop('surround_facilities')
            # 创建节点
            area_node = Node("located", **area_info)
            hotel_node = Node("hotel", **info)
            facility_node = Node("facilities", **facilities_info)
            policy_node = Node("policy", **policy_info)
            surround_node = Node("surround", **surround_info)
            self.connector.create(area_node | hotel_node | facility_node |
                                  policy_node | surround_node)
            self.connector.merge(
                    Relationship(area_node, 'isLocateOf', hotel_node)
                    | Relationship(hotel_node, 'hasFacilities', facility_node)
                    | Relationship(hotel_node, 'hasPolicy', policy_node)
                    | Relationship(hotel_node, 'hasSurround', surround_node))


# 测试代码：
if __name__ == '__main__':
    saver = CtripSaver()
    saver.data_save('HaikouHotels', 'SanyaHotels')
