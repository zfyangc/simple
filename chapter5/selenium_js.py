# coding:utf-8
import base64
import os
import re
import sqlite3
from http.cookiejar import CookieJar, LWPCookieJar
from io import BytesIO
from urllib import parse, request
from urllib.request import HTTPRedirectHandler

import lxml
import requests
import win32crypt
from PIL import Image
from lxml import html
from selenium import webdriver


def submit_fn():
    # 安装谷歌驱动
    driver = webdriver.Chrome()
    driver.get("http://example.webscraping.com/places/default/search")
    driver.find_element_by_id("search_term").send_keys('.')
    # js = "document.getElementById('page_size').options[1].text='1000'"
    # js = "$(#search.btn).click()"
    driver.find_element_by_id("search").click()
    # driver.execute_script(js)
    driver.implicitly_wait(200)
    links = driver.find_elements_by_css_selector('#results a')
    print(links)
    print([link.text for link in links])

    driver.close()


def form_fn():
    def parse_form_data():
        data = {}
        html_str = opener.open(login_url).read()
        tree = html.fromstring(html_str)
        for i in tree.cssselect("form input"):
            if i.get('name'):
                data[i.get('name')] = i.get("value")
        return data

    try:
        driver = webdriver.Chrome()
        login_url = "http://example.webscraping.com/places/default/user/login"
        driver.get(login_url)
        cj = CookieJar()
        opener = request.build_opener(request.HTTPCookieProcessor(cj))
        data = parse_form_data()
        data['email'] = 'example@webscraping.com'
        data["password"] = 'example'
        data.pop("remember_me")
        encode_data = parse.urlencode(data).encode(encoding='UTF8')
        form_tag = driver.find_element_by_css_selector("#web2py_user_form form")
        context_type = form_tag.get_attribute("enctype")
        dst_url = form_tag.get_attribute("action")
        header = {}
        if dst_url and dst_url == "#":
            dst_url = login_url
        if not context_type:
            header["content-type"] = context_type

        req = request.Request(login_url, data=encode_data, headers={"content-type": context_type})
        response = opener.open(req)
        print(response.geturl())
        print(response.getcode())
        get_cookie_from_session()

    except Exception as e:
        print(str(e))


# form_fn()
'''cookie的存放：
1、通过sqlite数据库
2、通过本地文件
从chrome浏览器中获取cookie sqlite'''


def get_cookie_from_chrome():
    def query_cookie_from_sqlite(host=".os.china.net"):
        cookiepath = os.environ['LOCALAPPDATA'] + r"\Google\Chrome\User Data\Default\Cookies"
        sql = "select name,encrypted_value from cookies where host_key='%s'" % host
        with sqlite3.connect(cookiepath) as conn:
            cu = conn.cursor()
            cookies = {}
            for name, encrypted_value in cu.execute(sql).fetchall():
                cookies[name] = win32crypt.CryptUnprotectData(encrypted_value)[1].decode()  # 解密cookie 信息

        print(cookies)
        return cookies

    # driver = webdriver.Chrome()
    login_url = "http://example.webscraping.com/places/default/user/login"
    print(request.urlopen(login_url).read())
    # driver.get(login_url)
    host_key = "example.webscraping.com"
    cookies = query_cookie_from_sqlite(host_key)
    print(cookies)
    cookie_str = ';'.join(['%s=%s' % (k, v) for k, v in cookies.items()])
    print(cookie_str)
    cj = CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cj))
    req = request.Request(login_url)
    cookie_str = re.sub('\n', '', cookie_str)
    req.add_header("Cookie", cookie_str)
    response = opener.open(req)
    print(response.read())
    print(response.getcode())


# get_cookie_from_chrome()

def get_cookie_from_session():
    req_session = requests.session()
    req_session.cookies = LWPCookieJar(filename='cookies')
    try:
        req_session.cookies.load(ignore_discard=True)
    except:
        print("Cookie 未能加载")

    # 保存 cookies 到文件，
    # 下次可以使用 cookie 直接登录，不需要输入账号和密码
    req_session.cookies.save()


# get_cookie_from_session()

# 使用mechanize 模块，可以容易的实现表单自动提交

def form_by_mechanize():
    import mechanize
    login_url = "http://example.webscraping.com/places/default/user/login"
    login_email = "example.webscraping.com"
    login_password = "example"
    br_obj = mechanize.Browser()
    br_obj.open(login_url)
    br_obj.select_form(nr=0)
    br_obj['email'] = login_email
    br_obj['password'] = login_password
    response = br_obj.submit()
    print(response.read())
    print(response.getcode())
    edit_url = ''
    br_obj.open(edit_url)
    br_obj.select_form(nr=0)
    br_obj['population'] = str(int(br_obj['population']) + 1)
    br_obj.submit()


# 增加验证码的功能识别功能， captcha(completely automated public turing test to tell computer and humans Apart)

def auto_register_with_captcha():
    import mechanize
    import pytesseract
    def get_image_captcha(html):
        tree = lxml.html.fromstring(html)
        img_data = tree.cssselect("div#recaptcha img")[0].get('src')
        img_data = img_data.partition(',')[-1]
        binary_img_data = base64.b64decode(img_data)
        # binary_img_data = img_data.decode('base64')
        file_like = BytesIO(binary_img_data)
        img = Image.open(file_like)
        return img

    def check_img(img):
        """使用pytesseract 光学字符识别模块，进行识别"""
        # 去除图像的背景噪音，就是背景像素
        gray = img.convert('L')
        # gray.save("captcha_gray.png")
        bw = gray.point(lambda x: 0 if x < 1 else 255, '1')
        # bw.save("captcha_thresholded.png")
        return pytesseract.image_to_string(bw)

    register_url = "http://example.webscraping.com/places/default/user/register"
    br_obj = mechanize.Browser()
    html = br_obj.open(register_url).read()
    img = get_image_captcha(html)
    captcha_str = check_img(img)
    print(captcha_str)
    register_email = "demo@webscraping.com"
    register_password = "demo"
    # print(br_obj)
    br_obj.select_form(nr=0)
    br_obj['email'] = register_email
    br_obj['password'] = register_password
    br_obj['password_two'] = register_password
    br_obj['first_name'] = 'd'
    br_obj['last_name'] = 'd'
    br_obj['recaptcha_response_field'] = captcha_str
    br_obj.submit()
    # login_url = "http://example.webscraping.com/places/default/user/login"
    # br_obj = mechanize.Browser()
    # br_obj.open(login_url)
    # br_obj.select_form(nr=0)
    # br_obj['email'] = register_email
    # br_obj['password'] = register_password
    # response = br_obj.submit()
    # print(response.getcode())
    # print(response.geturl())
# auto_register_with_captcha()

