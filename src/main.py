#!/usr/bin/env python

import argparse
import requests
import time
import re
import json
import random
from urllib.parse import urljoin
from pyquery import PyQuery as pq
from user_gent_list import USER_AGENT_LIST

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--intervals', type=int, help='网页下载间隔时间, 默认是3。')
recursion_parser = parser.add_mutually_exclusive_group(required=False)
recursion_parser.add_argument('-r', '--recursion', dest='recursion', help='递归获取子级。', action='store_true')
recursion_parser.add_argument('--no-recursion', dest='recursion', help='不递归获取子级，只获取直属子级，默认。', action='store_false')
parser.add_argument('-o', '--output', help='指定爬取的数据保存到的文件。')
parser.add_argument('-f', '--format', help='指定数据保存的格式，目前只支持 json。')
parser.add_argument('--adcode', help='指定要获取的城市的 adcode，将获取其下一级的 adcode 数据列表。')

parser.set_defaults(recursion=False)

args = parser.parse_args()

intervals = args.intervals if args.intervals else 3  # 防止太快的访问网站。
recursion = args.recursion  # 是否获取子级
fileFormat = args.format if args.format else 'json'
if fileFormat != 'json':
  raise Exception('不支持的文件格式[{}]'.format(fileFormat))
output = args.output if args.output else './output.{}'.format(fileFormat)

# print(intervals)
# print(recursion)
# print(fileFormat)
# print(output)
# print(args.adcode)

# 首页地址
indexUrl = 'http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2018/index.html'

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

def formatAdcode(adcode):
  '''
    格式化 adcode 长度固定为 12 位，不足的在后面补 0，超过的去掉后面的位
  '''
  if len(adcode) > 12:
    return adcode[0:12]
  else:
    zeros = ''
    for _ in range(12 - len(adcode)):
      zeros += '0'
    return adcode + zeros

def buildUrlFromAdcode(adcode):
  '''
    根据给定的 format 后的 adcode 构建其子级页面url
  '''
  url = 'http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2018/'
  province = adcode[0:2]  # 省 code
  city = adcode[2:4]  # 市
  county = adcode[4:6]  # 县区
  village = adcode[6:9] # 乡镇级
  finallyCode = ''
  if province != '00':
    finallyCode += province
  if city != '00':
    url += '{}/'.format(province)
    finallyCode += city
  if county != '00':
    url += '{}/'.format(city)
    finallyCode += county
  if village != '000':
    url += '{}/'.format(county)
    finallyCode += village
  url += '{}.html'.format(finallyCode)
  return url

def getDataListByUrl(url, key):
  '''
    省级以下，下载并解析页面数据。
  '''
  print(url)
  headers = { 'user-agent': random.choice(USER_AGENT_LIST) }
  nextR = requests.get(url, headers = headers)
  if (nextR.status_code != 200):
    print(nextR.text)
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
      time.sleep(intervals)
      recursionFetch(child['children'])

dataList = []
if args.adcode:
  enterUrl = buildUrlFromAdcode(formatAdcode(args.adcode))
  dataList = getDataListByUrl(enterUrl, getClassNameFromUrl(enterUrl))
else:
  # 获取省级数据
  r = requests.get(indexUrl)
  r.encoding = 'gb2312'
  q = pq(r.text)
  # 省级
  dataList = [{ 'code': a.attr('href')[0:2], 'name': a.text(), 'childrenUrl': urljoin(indexUrl, a.attr('href')) } for a in q('.provincetr td a').items('a')]

# 是否递归获取子级
if recursion:
  recursionFetch(dataList)

if fileFormat == 'json':
  with open(output, mode='w+', encoding="utf8") as f:
    f.write(json.dumps(dataList, ensure_ascii=False))
