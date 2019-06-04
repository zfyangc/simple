# coding:utf-8

import re


def pythonReSubDemo():
    """
        demo Pyton re.sub
    """
    inputStr = "hello 123 world 456"

    def _add111(matched):
        intStr = matched.group("number")  # 123
        intValue = int(intStr)
        addedValue = intValue + 111  # 234
        addedValueStr = str(addedValue)
        return addedValueStr

    replacedStr = re.sub("(?P<number>\d+)", _add111, inputStr)
    print "replacedStr=", replacedStr  # hello 234 world 567

if __name__ == '__main__':
    pythonReSubDemo()