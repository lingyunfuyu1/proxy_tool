# -*- coding: utf-8 -*-

import telnetlib

import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
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
        return self.protocol + '://' + ip + ':' + port

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
                    response = requests.get(url, proxies=proxies, timeout=timeout)
                elif method.lower() == 'post':
                    response = requests.post(url, data, proxies=proxies, timeout=timeout)
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


if __name__ == '__main__':
    proxies_tmp = []
    proxies_tmp.extend(get_proxies_from_crossincode())
    proxies_tmp.extend(get_proxies_from_xicidaili())
    proxies_tmp.extend(get_proxies_from_xiladaili())
    proxies = list(set(proxies_tmp))
    logger.info('Successfully got %s proxies in total' % str(len(proxies)))
    for (ip, port, protocol) in proxies:
        proxy = Proxy(ip, port, protocol)
        telnet_result = proxy.telnet_check(max_check_times=1, timeout=2)
        if not telnet_result:
            continue
        http_result = proxy.http_check('大明王朝1566', 'https://movie.douban.com/subject/2210001/', max_check_times=1, timeout=2)
        if not http_result:
            continue
        logger.info("'" + proxy.format() + "',")
