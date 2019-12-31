# -*- coding: utf-8 -*-
import requests
import os, sys
import re
import time
import threading
from aclass import *
from termcolor import colored

threadLock = threading.Lock()
stockPattern = re.compile(r'var hq_str_s[hz]\d{6}="([^,"]+),([^,"]+),([^,"]+),([^,"]+),[^"]+";')
distributionCount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # 20个对应的分布数量
distributionMaximum = 0 # 分布数量中最大的数量
totalIncrease = 0.0
totalCount = 0

def devideStockList(stockList):
	url = 'https://hq.sinajs.cn/list=' + ','.join(stockList)
	try:
		content = requests.get(url, timeout = 3).text
	except requests.exceptions.RequestException:
		return False
	global totalIncrease
	global totalCount
	threadLock.acquire()
	match = stockPattern.search(content)
	while match:
		stock = Stock(match.group(1), match.group(2), match.group(3), match.group(4))
		if stock.todayStart > 0 and stock.yesterdayEnd > 0:
			increase = (stock.current - stock.yesterdayEnd) / stock.yesterdayEnd * 100
			totalIncrease += increase
			totalCount += 1
			if increase > 9.999:
				increase = 9.999
			elif increase < -9.999:
				increase = -9.999
			increase = int(10 - increase)
			distributionCount[increase] = distributionCount[increase] + 1
		match = stockPattern.search(content, match.end())
	threadLock.release()
	return True

def threadFunction(stockList):
	while devideStockList(stockList) == False:
		pass

# 多线循环筛选所有股票数据
startTime = time.time()
if (os.path.isfile(os.path.join(sys.path[0], 'stock.list')) != True):
	print('请先运行avalid.py生成stock.list文件')
	exit(1)
validStockFile = open(os.path.join(sys.path[0], 'stock.list'), 'r')
validStockList = validStockFile.read().split('\n')
validStockFile.close()
countPerThread = 100
threadCount = (len(validStockList) + countPerThread - 1) // countPerThread
threadList = []
for index in range(0, threadCount):
	thread = threading.Thread(target = threadFunction, args = (validStockList[index * countPerThread:(index + 1) * countPerThread],))
	threadList.append(thread)
for thread in threadList:
	thread.start()
for thread in threadList:
	thread.join()
print('涨幅分布:')
for increase in range(0, 20):
	if distributionMaximum < distributionCount[increase]:
		distributionMaximum = distributionCount[increase]
for increase in range(0, 20):
	distributionStr = '{:4d} {}'.format(distributionCount[increase], '*' * (distributionCount[increase] * 70 // distributionMaximum))
	if increase < 8:
		distributionStr = colored(distributionStr, 'red')
	elif increase > 11:
		distributionStr = colored(distributionStr, 'green')
	print(distributionStr)
print('平均涨幅: {:.2f}%'.format(totalIncrease / totalCount))
print('开盘数量: {}'.format(totalCount))
localTime = time.localtime(startTime)
print('运行时间: {:02d}:{:02d}:{:02d}'.format(localTime.tm_hour, localTime.tm_min, localTime.tm_sec))
print('总 用 时: {:.2f}秒'.format(time.time() - startTime))
