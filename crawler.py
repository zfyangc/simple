# coding:utf-8
import csv
import os
import pickle
import random
import re
import robotparser
import time
import urllib
import urllib2
import urlparse

import lxml.html
from bs4 import BeautifulSoup


class spider_crawl(object):
    def __init__(self):
        pass

    def download(self, url, header, proxy, retries_count, data=None):
        print "start download url %s" % str(retries_count)
        retries_count += 1
        try:
            req = urllib2.Request(url, headers=header)

            # proxy = {
            #     "usr": '',
            #     "pass": '',
            #     "host": '',
            #     "port": ''
            # }

            proxy_str = "http://%(usr)s:%(pass)s@%(host)s:%(port)d" % proxy
            opener = urllib2.build_opener()
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
                return None

    def get_follow_url(self, base_html):
        pattern = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
        return pattern.findall(base_html)

    '''支持链路跟踪'''

    def link_crawler(self, baseUrl, regex, scrape_call_back=None, cache=None):
        base_html = self.download(baseUrl)
        if base_html:
            for f_url in self.get_follow_url(base_html):
                # print "follow urls %s" % f_url
                if re.match(regex, f_url):
                    f_url = urlparse.urljoin(baseUrl, f_url)
                    f_html = self.download(f_url)
                    if scrape_call_back and f_html:
                        scrape_call_back(f_url, f_html)

    '''支持安全网站爬虫'''

    def robot_paser(self, url):
        rp = robotparser.RobotFileParser()
        rp.set_url(urlparse.urljoin(url, '/robots.txt'))
        rp.read()

        return rp
        # user_agent = 'BadCrawler'
        # rp.can_fetch(user_agent, url)



    '''支持代理访问'''

    def check_proxy(self, url, request):
        proxy_info = {
            "usr": '',
            "pass": '',
            "host": '',
            "port": ''
        }
        proxy_str = "http://%(usr)s:%(pass)s@%(host)s:%(port)d" % proxy_info
        opener = urllib2.build_opener()
        proxy_params = {urllib.urlparse(url).scheme: proxy_str}
        opener.add_handler(urllib2.ProxyHandler(proxy_params))
        response = opener.open(request)

    '''避免爬虫程序进入死循环，这种叫爬虫陷阱'''

    def avoid_spider_trap(self):
        # 策略是：设置每个访问过的网址的次数
        pass

    # spider_crawl().link_crawler("http://example.webscraping.com/places/default", r'/(index|view)')

    '''解析html字符，抓取关键信息'''

    def regex_parse(self):
        pass

    def beautifulSoup_parse(self):
        url = "http://example.webscraping.com/places/default/view/Angola-7"
        html_str = self.download(url)
        # soup = BeautifulSoup(html_str, 'html.parser')
        # html_str = soup.prettify()
        fixed_soup = BeautifulSoup(html_str)
        tr = fixed_soup.find(attrs={'id': 'places_area__row'})
        td = tr.find(attrs={"class": 'w2p_fw'})
        area = td.text
        print area

    def lxml_parse(self):
        url = 'http://example.webscraping.com/places/default/view/Angola-7'
        html_str = self.download(url)
        html_element_tree = lxml.html.fromstring(html_str)
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


# spider_crawl().beautifulSoup_parse()
# spider_crawl().lxml_parse()
# spider_crawl().link_crawler('http://example.webscraping.com/', '/places/default/(index|view)', scrape_call_back=ScrapeCallBack())

'''设置下载缓存和控制下载速度'''


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


class DownloadObj(object):
    def __init__(self, delay=5, user_agent="wswp", proxies=None, retries_count=1, cache=None):
        self.throttle = Throttle(delay)
        self.user_agent = user_agent
        self.proxies = proxies
        self.retries_count = retries_count
        self.cache = cache

    def download(self, url, header, proxy, retries_count, data=None):
        print "start download url %s" % str(retries_count)
        retries_count += 1
        try:
            req = urllib2.Request(url, headers=header)

            # proxy = {
            #     "usr": '',
            #     "pass": '',
            #     "host": '',
            #     "port": ''
            # }

            proxy_str = "http://%(usr)s:%(pass)s@%(host)s:%(port)d" % proxy
            opener = urllib2.build_opener()
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
                return None

    def __call__(self, url):
        if self.cache:
            try:
                result = self.cache[url]
            except KeyError as e:
                print "url is not available in cache"
            else:
                if self.retries_count > 0 and 500 < result['code'] < 600:
                    result = None
        if not result:
            self.throttle.wait(url)
            proxy = random.choice(self.proxies) if self.proxies else None
            header = {'User-agent': self.user_agent}
            result = self.download(url, header, proxy, self.retries_count)
            if self.cache and result:
                self.cache[url] = result
        return result.get("html") if result else None


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
            raise Exception(url+"does not exist!")


    def __setitem__(self, url, result):
        path = self.gen_cache_path(url)
        folder = os.path.dirname(path)
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(path, 'wb') as fw:
            pickle.dump(result, fw)
if __name__ == '__main__':
   spider_crawl().link_crawler('http://example.webscraping.com/', '/(index|view)', cache=Diskcache())