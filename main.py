#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
财经网爬取
@author: github.com/zhengxiaoyao0716
"""

from collections import namedtuple
import logging
import requests
from bs4 import BeautifulSoup

# 配置
config = namedtuple('Config', (
    'pages',  # 待爬取页面
    'encoding',  # 页面编码
    'output',  # 输出路径
))(
    (
        'http://www.caijing.com.cn/dailynews/index.html',
        *('http://www.caijing.com.cn/dailynews/index-%d.html' % (6199 - index)
          for index in range(10)),
    ),
    'utf-8',
    'output.txt',
)


def parse(soup: BeautifulSoup):
    """解析页面数据"""
    items = soup.select_one('div.main_lt').select_one('ul.list').select('li')

    def pick(item, cls):
        """摘取指定文本"""
        return item.select_one('div.' + cls).text.strip()
    return ({
        'title': pick(item, 'wzbt'),
        'date': pick(item, 'time'),
        'subtitle': pick(item, 'subtitle'),
    } for item in items)


def fetch(url: str):
    """抓取页面"""
    print('正在抓取 `%s`:' % url)
    resp = requests.get(url)  # 请求页面
    resp.encoding = 'utf-8'  # 设置响应编码
    soup = BeautifulSoup(resp.text, 'lxml')  # 读取页面内容
    try:
        data = parse(soup)
    except Exception as e:  # pylint: disable=W0703
        logging.error('解析失败，请检查目标页面格式并修正解析器')
        logging.exception(e)
        return []
    print('成功\n')
    return data


def export(data: list):
    """导出数据"""
    text = '\n\n'.join(
        '\n'.join((
            'Title: ' + item['title'],
            'Date: ' + item['date'],
            'Subtitle: ' + item['subtitle'],
        )) for item in data
    ) + '\n'
    # 写入文件
    with open(config.output, 'w', encoding='utf-8') as file:
        file.write(text)
    print('共 %d 条数据抓取完成，数据已导出到 `%s`.' % (len(data), config.output))


def main():
    """Entrypoint"""
    data = [item for url in config.pages for item in fetch(url)]
    data and export(data)  # pylint: disable=W0106


if __name__ == '__main__':
    main()
