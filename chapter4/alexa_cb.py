# -*- coding: utf-8 -*-

import csv
from zipfile import ZipFile
from StringIO import StringIO
from mongo_cache import MongoCache


class AlexaCallback:
    def __init__(self):
        pass

    def __call__(self):
        urls = []
        with open(r"C:\Users\yangzhengfang\Downloads\top-1m.csv", 'r') as csvFile:
            rows = csv.reader(csvFile)
            urls.extend(["https://www." + r for _, r in rows])

        return urls
