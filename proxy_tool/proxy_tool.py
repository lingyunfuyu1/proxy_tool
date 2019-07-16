# -*- coding: utf-8 -*-
import sys
import telnetlib

import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Host': '',
    'Referer': '',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
}


class ParamError(object):
    pass


class Proxy(object):
    def __init__(self, ip, port, protocol='http'):
        self.ip = ip
        self.port = port
        self.protocol = protocol

    def format(self):
        return self.protocol + '://' + self.ip + ':' + self.port

    def telnet_check(self, max_check_times=3, timeout=3):
        for i in range(max_check_times):
            try:
                telnetlib.Telnet(self.ip, port=self.port, timeout=timeout)
                return True
            except:
                pass
        return False

    def http_check(self, expect, url, data=None, additional_headers=None, method='get', max_check_times=3, timeout=3):
        if not expect or not url:
            raise ParamError
        if data and not isinstance(dict, data):
            raise ParamError
        if additional_headers and not isinstance(dict, additional_headers):
            raise ParamError
        if method.lower() not in ['get', 'post']:
            raise ParamError
        if data is None:
            data = {}
        if additional_headers is None:
            additional_headers = {}
        result = urlparse(url)
        headers['Host'] = result.netloc
        headers['Referer'] = result.scheme + '://' + result.netloc + '/'
        if list(additional_headers.keys()):
            for key in additional_headers.keys():
                headers[key] = additional_headers.get(key)
        proxies = {
            'http': self.protocol + '://' + self.ip + ':' + self.port,
            'https': self.protocol + '://' + self.ip + ':' + self.port,
        }
        for i in range(max_check_times):
            try:
                response = ''
                if method.lower() == 'get':
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                elif method.lower() == 'post':
                    response = requests.post(url, data, headers=headers, proxies=proxies, timeout=timeout)
                if response.text.find(expect) != -1:
                    return True
            except:
                pass
        return False


def get_proxies_from_crossincode():
    url = 'https://lab.crossincode.com/proxy/'
    proxies = []
    try:
        logger.info('Getting proxies from %s...' % url)
        result = urlparse(url)
        headers['Host'] = result.netloc
        headers['Referer'] = result.scheme + '://' + result.netloc + '/'
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        trs = soup.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) < 6:
                continue
            protocol = tds[3].string.lower()
            if protocol not in ['http', 'https', 'http,https']:
                continue
            if protocol.find(',') != -1:
                protocol = protocol.split(',')[0]
            proxies.append((tds[0].string, tds[1].string, protocol))
        logger.info('Successfully got %s proxies from %s' % (str(len(proxies)), url))
        return proxies
    except:
        logger.info('Exception occurd when getting proxies from %s' % url)
        return proxies


def get_proxies_from_xicidaili():
    url = 'https://www.xicidaili.com/'
    proxies = []
    try:
        logger.info('Getting proxies from %s...' % url)
        result = urlparse(url)
        headers['Host'] = result.netloc
        headers['Referer'] = result.scheme + '://' + result.netloc + '/'
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        trs = soup.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) < 8:
                continue
            if tds[5].string.lower() not in ['http', 'https']:
                continue
            proxies.append((tds[1].string, tds[2].string, tds[5].string.lower()))
        logger.info('Successfully got %s proxies from %s' % (str(len(proxies)), url))
        return proxies
    except:
        logger.info('Exception occurd when getting proxies from %s' % url)
        return proxies


def get_proxies_from_xiladaili():
    url = 'http://www.xiladaili.com/'
    proxies = []
    try:
        logger.info('Getting proxies from %s...' % url)
        result = urlparse(url)
        headers['Host'] = result.netloc
        headers['Referer'] = result.scheme + '://' + result.netloc + '/'
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        trs = soup.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) < 8:
                continue
            protocol = tds[2].string.lower()
            if protocol not in ['http', 'https', 'http,https']:
                continue
            if protocol.find(',') != -1:
                protocol = protocol.split(',')[0]
            proxies.append((tds[0].string.split(':')[0], tds[0].string.split(':')[1], protocol))
        logger.info('Successfully got %s proxies from %s' % (str(len(proxies)), url))
        return proxies
    except:
        logger.info('Exception occurd when getting proxies from %s' % url)
        return proxies


def main(expect, url, data=None, additional_headers=None, method='get', max_check_times=3, timeout=3):
    proxies_tmp = []
    proxies_tmp.extend(get_proxies_from_crossincode())
    proxies_tmp.extend(get_proxies_from_xicidaili())
    proxies_tmp.extend(get_proxies_from_xiladaili())
    proxies = list(set(proxies_tmp))
    logger.info('Successfully got %s proxies in total' % str(len(proxies)))
    results = []
    for (ip, port, protocol) in proxies:
        proxy = Proxy(ip, port, protocol)
        telnet_result = proxy.telnet_check(max_check_times=max_check_times, timeout=timeout)
        http_result = ''
        if telnet_result:
            http_result = proxy.http_check(expect, url, data=data, additional_headers=additional_headers, method=method, max_check_times=max_check_times, timeout=timeout)
        logger.info('%s  telnet_check:%s  http_check:%s' % (proxy.format(), telnet_result, http_result))
        if not telnet_result or not http_result:
            continue
        results.append("'" + proxy.format() + "',")
    for result in results:
        print(result)


def test(expect, url, proxy, data=None, additional_headers=None, method='get'):
    if data is None:
        data = {}
    if additional_headers is None:
        additional_headers = {}
    result = urlparse(url)
    headers['Host'] = result.netloc
    headers['Referer'] = result.scheme + '://' + result.netloc + '/'
    if list(additional_headers.keys()):
        for key in additional_headers.keys():
            headers[key] = additional_headers.get(key)
    proxies = {
        'http': proxy,
        'https': proxy,
    }
    try:
        response = ''
        if method.lower() == 'get':
            response = requests.get(url, headers=headers, proxies=proxies)
        elif method.lower() == 'post':
            response = requests.post(url, data, headers=headers, proxies=proxies)
        print(response.text)
        if response.text.find(expect) != -1:
            print('Success')
        else:
            print('Failed')
    except:
        print("Unexpected error:", sys.exc_info()[0])


if __name__ == '__main__':
    # 豆瓣
    # expect = '大明王朝1566'
    # url = 'https://movie.douban.com/subject/2210001/'
    # 知乎
    expect = '书籍推荐'
    url = 'https://www.zhihu.com/question/22818974'
    # 获取代理
    main(expect, url)
    # 测试代理
    # proxy = 'https://140.143.48.49:1080'
    # test(expect, url, proxy)
