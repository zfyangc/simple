# coding:utf-8

####pickle 模块：可以将序列化的对象存储到磁盘中，可以将任何对象序列化

import pickle
import json


# dumps 函数
def test_pickle_dumps():
    dumps_obj = {"a": '1', "b": "2", "c": "3"}
    p = pickle.dumps(dumps_obj)
    print p
    print pickle.loads(p)

# test_pickle_dumps()

def test_pickle_dump():
    dumps_obj = {"a": '1', "b": "2", "c": "3"}
    with open("s.txt", 'wb') as fw:
        pickle.dump(dumps_obj, fw)
# test_pickle_dump()

def test_pickle_load():
    with open("s.txt", "rb") as fr:
        print pickle.load(fr)
# test_pickle_load()

def test_json_dumps():
    # a = {"a": '1', "b": "2", "c": "3"}
    a = [1,2,3,4]   # 这里的obj可以为任何的数据格式
    print type(json.dumps(a)),json.dumps(a)


# test_json_dumps()
def test_json_loads():
    a = '{"a": "1", "b": "2", "c": "3"}'
    # a = "{'a': '1', 'b': '2', 'c': 3'}"  # 错误的结构
    print json.loads(a)
# test_json_loads()

def test_json_dump():
    a=[1,2,3,4,5]
    with open('a.txt', 'wb') as fw:
        json.dump(a, fw)   # 变成文件流
# test_json_dump()

def test_json_load():
    with open("a.txt", 'rb') as fr:
        print json.load(fr)
# test_json_load()