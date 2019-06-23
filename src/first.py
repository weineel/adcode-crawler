#!/usr/bin/env python

import argparse
import requests
import time
import re
from urllib.parse import urljoin
from pyquery import PyQuery as pq
import json

sleepTime = 2  # 防止太快的访问网站。

entryUrl = 'http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2018/index.html'

parser = argparse.ArgumentParser()

global classNameTable
classNameTable = {
  2: 'citytr',  # 市级
  4: 'countytr', # 县区级
  6: 'towntr',  # 乡镇级
  9: 'villagetr', # 村级
}

def getClassNameFromUrl(url):
  global classNameTable
  code = re.search('(?<=\/)\d*?(?=\.html)', url)
  if code != None:
    pos = code.span()
    key = pos[1] - pos[0]
    return classNameTable[key]
  else:
    return ''


def getDataListByUrl(url, key):
  '''
    省级以下，下载并解析页面数据。
  '''
  print(url)
  nextR = requests.get(url)
  if (nextR.status_code != 200):
    return []
  nextR.encoding = 'gb2312'
  q = pq(nextR.text)
  # 获取 code
  dataList = []
  codeQuery = q('.{} td:first-child'.format(key))
  for tdItem in codeQuery:
      # 虽然仅有一条数据，但是仍然需要通过 for 获取
      aData = [{ 'code': a.text() } for a in pq(tdItem).items('a')]
      if(len(aData) <= 0):
        # 没有 a 标签
        aData = [{ 'code': td.text() } for td in pq(tdItem).items('td')]
      dataList += aData

  # 插入 code 对应的地理位置名称
  for i, cityNameItem in enumerate(q('.{} td:last-child'.format(key))):
    aDataName = [{ 'name': a.text(), 'childrenUrl': urljoin(nextR.url, a.attr('href')) } for a in pq(cityNameItem).items('a')]
    if(len(aDataName) <= 0):
      # 没有 a 标签
      aDataName = [{ 'name': td.text(), 'childrenUrl': None } for td in pq(cityNameItem).items('td')]
    dataList[i]['name'] = aDataName[0]['name']
    # 下一级url
    dataList[i]['childrenUrl'] = aDataName[0]['childrenUrl']

  for item in dataList:
    print('{} -> {}'.format(item['code'], item['name']))
  return dataList

def recursionFetch(parentDataList):
  ''' 一级级向下获取所有数据 '''
  for child in parentDataList:
    if child['childrenUrl'] != None:
      dataList = getDataListByUrl(child['childrenUrl'], getClassNameFromUrl(child['childrenUrl']))
      child['children'] = dataList
      time.sleep(sleepTime)
      recursionFetch(child['children'])

# 获取省级数据
r = requests.get(entryUrl)
r.encoding = 'gb2312'
q = pq(r.text)
provinces = [{ 'code': a.attr('href')[0:2], 'name': a.text(), 'childrenUrl': urljoin(entryUrl, a.attr('href')) } for a in q('.provincetr td a').items('a')]

recursionFetch(provinces)

with open('./result.json', mode='w+') as f:
  f.write(json.dumps(provinces))

def buildUrlWithCode(code):
  pass

parser.parse_args()
