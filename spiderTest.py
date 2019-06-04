# coding:utf-8
import csv
import datetime
import os
import pickle
import random
import re
import robotparser
import shutil
import time
import urllib
import urllib2
import urlparse

# 下载类的封装，主要是为了模块化
import zlib
from StringIO import StringIO
from collections import defaultdict
from datetime import timedelta
from threading import Thread
from zipfile import ZipFile

import lxml.html
from bs4 import BeautifulSoup
from bson import Binary
from pymongo import MongoClient
from pymongo.errors import OperationFailure

'''数据下载器'''


class Downloader(object):

    def __init__(self, delay=5, user_agent="wswp", proxies=None, retries_count=0, cache=None):
        self.throttle = Throttle(delay)
        self.user_agent = user_agent
        self.proxies = proxies
        self.retries_count = retries_count
        self.cache = cache

    def __call__(self, url):
        result = None
        if self.cache:
            try:
                result = self.cache[url]
            except KeyError as e:
                print "url is not available in cache %s" % e.message

        # 当下载网页时失败，需要再次下载
        if result and self.retries_count > 0 and 500 <= result['code'] < 600 or result is None:
            # self.throttle.wait(url)
            if self.proxies:
                proxy = random.choice(self.proxies)
            else:
                proxy = None
            header = {'User-agent': self.user_agent}
            result = self.download(url, header, proxy, self.retries_count)
            if self.cache and result:
                self.cache[url] = result
        return result.get("html") if result else None

    def download(self, url, header={}, proxy=None, retries_count=0):
        print "start download %s" % url
        retries_count += 1
        try:
            req = urllib2.Request(url, headers=header)
            opener = urllib2.build_opener()
            # proxy = {
            #     "usr": '',
            #     "pass": '',
            #     "host": '',
            #     "port": ''
            # }
            if proxy:
                proxy_str = "http://%(usr)s:%(pass)s@%(host)s:%(port)d" % proxy
                proxy_params = {urllib.urlparse(url).scheme: proxy_str}
                opener.add_handler(urllib2.ProxyHandler(proxy_params))
            response = opener.open(req)
            rsp_html = response.read()
            return {"html": rsp_html, "code": response.code}
        except urllib2.URLError as e:
            if hasattr(e, "code") and e.code >= 500 and e.code < 600 and retries_count < 5:
                return self.download(url, retries_count)
            else:
                print "urllib2.URLError: %s" % e.message

    def get_follow_url(self, html):
        pattern = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
        return pattern.findall(html)

    '''支持安全网站爬虫'''

    def robot_paser(self, url, user_agent):
        rp = robotparser.RobotFileParser()
        rp.set_url(urlparse.urljoin(url, '/robots.txt'))
        rp.read()
        # user_agent = 'BadCrawler'
        return rp.can_fetch(user_agent, url)


'''延时器'''


class Throttle(object):
    def __init__(self, delay=None):
        self.delay = delay
        self.domain_dict = {}

    def wait(self, url):
        domain = urlparse.urlparse(url).netloc
        last_timestamp = self.domain_dict.get(domain)
        if self.delay and last_timestamp:
            time_delta = time.mktime(time.localtime()) - last_timestamp
            if 0 < time_delta < 5:
                time.sleep(self.delay - time_delta)

            self.domain_dict[domain] = time.mktime(time.localtime())


'''存储爬取的数据到csv文件'''


class ScrapeCallBack:
    def __init__(self):
        self.writer = csv.writer(open("scrapeData.csv", 'w'))
        self.fileds = ("area", 'population', 'iso', 'country', 'currency_name', 'continent', 'tld', 'currency_code')
        self.writer.writerow(self.fileds)

    def __call__(self, url, html, **kwargs):
        '''__call__ 函数是用来表明对象的特殊功能，将类变成了可调用对象，当类的实例被当作函数调用的时候，调用这个函数'''
        if re.search("/view", url):
            tree = lxml.html.fromstring(html)
            row = []
            for filed in self.fileds:
                row.append(tree.cssselect('table>tr#places_{}__row>td.w2p_fw'.format(filed))[0].text_content())
            self.writer.writerow(row)


'''数据解析器'''


class crawler(object):
    def __init__(self, cache):
        self.cache = cache

    def beautifulSoup_parse(self, html):
        # url = "http://example.webscraping.com/places/default/view/Angola-7"
        # html_str = self.download(url)
        # soup = BeautifulSoup(html_str, 'html.parser')
        # html_str = soup.prettify()
        fixed_soup = BeautifulSoup(html)
        tr = fixed_soup.find(attrs={'id': 'places_area__row'})
        td = tr.find(attrs={"class": 'w2p_fw'})
        area = td.text
        print area
        return area

    def lxml_parse(self, html):
        # url = 'http://example.webscraping.com/places/default/view/Angola-7'
        # html_str = self.download(url)
        html_element_tree = lxml.html.fromstring(html)
        fixed_html = lxml.html.tostring(html_element_tree, pretty_print=True)
        print fixed_html
        element_tree = lxml.html.fromstring(fixed_html)
        td = element_tree.cssselect("tr#places_area__row > td.w2p_fw")[0]
        # css 选择器的书写格式为：
        # 1、根据标签属性匹配：a[Title=Home]
        # 2、根据class 名或id 匹配： a#link a.link
        # 3、根据父元素来匹配： a > span
        # 4、根据包含关系匹配：a span
        area = td.text_content()
        print area
        return area


'''磁盘存储器'''


class Diskcache(object):
    def __init__(self, cache_dir='cache', max_length=255):
        self.cache_dir = cache_dir
        self.max_length = max_length

    def gen_cache_path(self, url):
        components = urlparse.urlsplit(url)
        path = components.path
        if not path:
            path = "/index.html"
        elif path.endswith('/'):
            path += "index.html"

        filename = components.netloc + components.path + components.query
        filename = re.sub("[^0-9a-zA-Z\-.;_]", '_', filename)
        if filename:
            filename = '/'.join(i[:self.max_length] for i in filename.split('/'))
        return os.path.join(self.cache_dir, filename)

    def __getitem__(self, url):
        '''load data from disk file system for this url'''
        path = self.gen_cache_path(url)
        if os.path.exists(path):
            with open(path, 'rb') as fb:
                return pickle.load(fb)
        else:
            raise Exception(url + "does not exist!")

    def __setitem__(self, url, result):
        path = self.gen_cache_path(url)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(path, 'wb') as fw:
            pickle.dump(result, fw)

    def clear(self):
        """Remove all the cached values
        """
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)


def link_crawler(url, regex, user_agent, cache=None, spider_callback=None, max_depth=1):
    # 获取原路径的页面信息
    downloader = Downloader(user_agent=user_agent, cache=cache)
    # 通过网站安全爬虫，才执行下载功能
    url_depth = defaultdict(lambda: 0)
    if downloader.robot_paser(url, user_agent):
        # 检查重复的url
        if url_depth.get(url) != max_depth:
            download_res = downloader(url)
            url_depth[url] += 1
            if download_res:
                if cache:
                    cache[url] = download_res
                    # 将页面数据存储到csv文件中
                    if spider_callback:
                        spider_callback(url, download_res['html'])

                    for furl in downloader.get_follow_url(download_res['html']):
                        if re.match(regex, furl):
                            fullUrl = urlparse.urljoin(url, furl)
                            if url_depth.get(fullUrl) != max_depth:
                                followRes = downloader(fullUrl)
                                if followRes:
                                    url_depth[url] += 1
                                    cache[fullUrl] = followRes

                                    # 将页面数据存储到csv文件中
                                    if spider_callback:
                                        spider_callback(fullUrl, followRes['html'])


# if __name__ == '__main__':
# cache = Diskcache()
# link_crawler('http://example.webscraping.com', '/(index|view)', 'GoodCrawler', max_depth=1, cache=cache)


'''采用mongodb来储存数据'''


class mongodbCache(object):
    mongo_client = MongoClient(host='localhost', port=27017)
    db = mongo_client.config
    cache_db = db.cache

    def __init__(self, expires=timedelta(days=30)):
        if 'timestamp_1' in [i['name'] for i in self.cache_db.list_indexes()]:
            print "cache timestamp index is already exist!"
        else:
            self.cache_db.create_index('timestamp', expireAfterSeconds=expires.total_seconds())

    def __getitem__(self, url):
        """从数据库中获取数据"""
        cache_data = self.cache_db.find_one({"_id": url})
        if cache_data:
            # 解压缩 zip数据，并加载成原来的数据格式， decompress 函数可以直接将二进制数转成字节流类型
            return pickle.loads(zlib.decompress(cache_data['html']))
        else:
            raise KeyError(url + ' does not exist!')

    def __setitem__(self, url, html_info):
        """save html info to mongodb collection"""
        bhtml = Binary(zlib.compress(pickle.dumps(html_info['html'])))
        insert_data = {"html": bhtml, "code": html_info['code'], 'timestamp':datetime.datetime.utcnow()}
        self.cache_db.insert_one(insert_data)
        self.cache_db.update({'_id': url}, {'$set': insert_data}, upsert=True)


# mongodbcache = mongodbCache(expires=timedelta())
# html_info = {"html": 'sdsadadasad', "code": 200}
# mongodbcache['http://example.webscraping.com'] = html_info
# print mongodbcache['http://example.webscraping.com']



############并发爬虫###############
# 爬取100多个页面的数据信息，需要并发来实现
# 1、下载zip 文件
# 2、解析zip文件中的csv 表格
# 3、遍历csv 文件
class AlexaWebsite(object):
    def __init__(self):
        pass

    def __call__(self, url):
        # url = "http://s3.amazonaws.com/alexa-static/top-1m.csv.zip"
        # url = "http://example.webscraping.com/"
        # D = Downloader()
        # zipped_data = D(url)
        # print zipped_data
        urls = []
        with open(r"C:\Users\yangzhengfang\Downloads\top-1m.csv", 'r') as csvFile:
            rows = csv.reader(csvFile)
            urls = ["https://www."+r for _, r in rows]

        # with open('a.txt', 'w') as fw:
        #     for u in urls:
        #         u += '\n'
        #         fw.write(u)
        return urls

def Concurrent_crawler(alexa_url, user_agent, proxies=None, max_thread=10, cache=None, spider_callback=None, max_depth=1):
    def process_queue():
        while True:
            try:
                url = urls.pop()
            except IndexError as e:
                print e.message
                break
            else:
                if depth_record.get(url) < max_depth:
                    html_info = D(url)
                    print "do process queue"
                    depth_record[url] += 1

    SLEEP_TIME = 1
    depth_record = defaultdict(lambda: 0)
    D = Downloader(user_agent=user_agent, proxies=proxies, retries_count=0, cache=cache)
    if spider_callback:
        urls = spider_callback(alexa_url)
        threads = []
        if threads or urls:
            for thread in threads:
                if not thread.is_alive():
                    threads.remove(thread)

            while len(threads) < max_thread and urls:
                new_thread = Thread(target=process_queue)
                new_thread.setDaemon(True)
                new_thread.start()
                threads.append(new_thread)
            time.sleep(SLEEP_TIME)

mongocache = mongodbCache()
alexaWeb_cllaback = AlexaWebsite()
# alexaWeb_cllaback("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip")
Concurrent_crawler("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip",'wswp', max_thread=10, cache=mongocache, spider_callback=alexaWeb_cllaback, max_depth=1)