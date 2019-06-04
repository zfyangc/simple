# coding:utf-8
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# 简单的从页面上获取隐藏的js 请求链接  javascript的逆向工程


# 复杂的动态加载内容，javascript 代码被加密压缩的，需要使用渲染的方式来还原javascript代码

js_code = '''<html><body><div id="result"></div><script>document.getElementById("result").innerText=''hello world';</script></body></html>'''

app = QApplication([])







