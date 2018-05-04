#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
财经网爬取
@author: github.com/zhengxiaoyao0716
"""

import json
from collections import namedtuple
import logging
import requests
from bs4 import BeautifulSoup


def pick(item: BeautifulSoup, selector: str):
    """摘取指定文本"""
    field = item.select_one(selector)
    return field.text.strip() if field else ''


def parse_caijing(resp: requests.Response):
    """解析页面数据"""
    resp.encoding = 'utf-8'  # 设置响应编码
    soup = BeautifulSoup(resp.text, 'lxml')  # 读取页面内容
    items = soup.select_one('div.main_lt').select_one('ul.list').select('li')

    return ({
        'title': pick(item, 'div.wzbt'),
        'date': pick(item, 'div.time'),
        'subtitle': pick(item, 'div.subtitle'),
    } for item in items)


def parse_jingji(resp: requests.Response):
    """中国经济网解析页面数据"""
    resp.encoding = 'utf-8'  # 设置响应编码
    soup = BeautifulSoup(resp.text, 'lxml')  # 读取页面内容
    items = soup.select_one('div.neirong').select('table')[1] \
        .select_one('td').select('td')

    return ({
        'title': pick(item, 'a'),
        'date': pick(item, 'span.rq1'),
    } for item in items)


def parse_sina(resp: requests.Response):
    """解析新浪财经数据"""
    items = json.loads(resp.text)
    return ({
        'title': item['title'],
        'subtitle': item['intro'],
    } for item in items['result']['data'])



# 配置
config = namedtuple('Config', (
    'pages',  # 待爬取页面
    'encoding',  # 页面编码
    'keywords',  # 关键词
    'output',  # 输出路径
))(
    {  # parser: (url, url, url, ...)
        parse_caijing: (
            'http://www.caijing.com.cn/dailynews/index.html',
            *('http://www.caijing.com.cn/dailynews/index-%d.html' % (6199 - index)
              for index in range(10)),
        ),
        parse_sina: (
            'http://feed.mix.sina.com.cn/api/roll/get?'
            'pageid=155&lid=%d&num=10&page=%d' % (lid, page)
            for lid in (1686, 1687, 1690, 1688, 1689)
            for page in range(10)
        ),
        'yyy': (
        ),
    },
    'utf-8',
    ('关', '键', '词'),
    'output.txt',
)


def fetch(parse, url: str):
    """抓取页面"""
    print('正在抓取 `%s`:' % url)
    resp = requests.get(url)  # 请求页面
    try:
        data = parse(resp)
    except Exception as e:  # pylint: disable=W0703
        logging.error('解析失败，请检查目标页面格式并修正解析器')
        logging.exception(e)
        return []
    print('成功\n')
    return data


def export(data: list):
    """导出数据"""
    counter = {}

    def analyze(text: str):
        """分析文本是否包含关键词"""
        for kw in config.keywords:
            if text.find(kw) != -1:  # 文本中包含关键词
                counter[kw] = 1 + counter.get(kw, 0)
        return text

    text = '\n\n'.join(
        '\n'.join((
            'Title: ' + analyze(item.get('title', '')),
            'Date: ' + item.get('date', ''),
            'Subtitle: ' + analyze(item.get('subtitle', '')),
        )) for item in data
    ) + '\n'

    report = '关键词统计：\n' + \
        '\n'.join(('%s: %d 次' % (kw, counter[kw]) for kw in counter)) + \
        '\n总计: %d 次' % sum((counter[kw] for kw in counter))
    text = report + '\n\n' + text
    # 写入文件
    with open(config.output, 'w', encoding='utf-8') as file:
        file.write(text)
    print('共 %d 条数据抓取完成，数据已导出到 `%s`.' % (len(data), config.output))
    print(report)


def main():
    """Entrypoint"""
    data = [item
            for parse in config.pages
            for url in config.pages[parse]
            for item in fetch(parse, url)]
    data and export(data)  # pylint: disable=W0106


if __name__ == '__main__':
    main()
