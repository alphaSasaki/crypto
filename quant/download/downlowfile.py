import os

from urllib.request import urlretrieve
import socket

timeList = ['2021-05']
socket.setdefaulttimeout(30.0)
coin = 'ETH'

for t in timeList:
    image_url = ("https://data.binance.vision/data/spot/monthly/klines/%sUSDT/1h/%sUSDT-1h-%s.zip" % (coin, coin, t))
    print(image_url)
    urlretrieve(image_url, ('xxxx\\biandata\%s\%sUSDT-1h-%s.zip' % (coin.lower(), coin, t)))  # 将什么文件存放到什么位置
