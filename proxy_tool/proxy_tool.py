# -*- coding: utf-8 -*-
import logging
import telnetlib
import time
import traceback
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# 通用HTTP请求头
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
        """
        通过telnet方式检测代理端口是否可以连通
        :param max_check_times: 最大检测次数，只要有一次检测成功就返回成功，每次都检测失败才返回失败，非必传，默认为3
        :param timeout: 超时时间，单位为秒，非必传，默认为3
        :return: True-检测成功，False-检测失败
        """
        for i in range(max_check_times):
            try:
                telnetlib.Telnet(self.ip, port=self.port, timeout=timeout)
                return True
            except Exception as e:
                logger.debug('发生未知异常：' + traceback.format_exc())
        return False

    def http_check(self, expect, url, data=None, additional_headers=None, method='GET', max_check_times=3, timeout=3):
        """
        通过发送经由代理的http请求来检测响应内容是否包含预期信息。
        :param expect: 预期字符串，从响应内容查找是否存在该字符串以判断检测是否成功，必传
        :param url: 请求URL，必传
        :param data: 请求参数，非必传，传入时应为字典格式
        :param additional_headers: 附加请求头，作为默认请求头的补充，比如Cookie等，非必传，传入时应为字典格式
        :param method: 请求方法，非必传，默认为GET，传入时只能为GET或POST
        :param max_check_times: 最大检测次数，只要有一次检测成功就返回成功，每次都检测失败才返回失败，非必传，默认为3
        :param timeout: 超时时间，单位为秒，非必传，默认为3
        :return: True-检测成功，False-检测失败
        """
        # 参数检查
        if not expect or not url:
            raise ParamError
        if data and not isinstance(dict, data):
            raise ParamError
        if additional_headers and not isinstance(dict, additional_headers):
            raise ParamError
        if method.upper() not in ['GET', 'POST']:
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
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
                elif method.upper() == 'POST':
                    response = requests.post(url, data, headers=headers, proxies=proxies, timeout=timeout)
                if response.text.find(expect) != -1:
                    return True
                else:
                    logger.debug('查找失败！HTTP响应内容为：\n' + response.text)
            except Exception as e:
                logger.debug('发生未知异常：' + traceback.format_exc())
        return False


def get_proxies(urls):
    proxies = []
    for url in urls:
        try:
            logger.info('正在从%s获取代理...' % url)
            result = urlparse(url)
            headers['Host'] = result.netloc
            headers['Referer'] = result.scheme + '://' + result.netloc + '/'
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            if url.find('xicidaili') != -1:
                tmp_proxies = get_proxies_from_xicidaili(soup)
            elif url.find('xiladaili') != -1:
                tmp_proxies = get_proxies_from_xiladaili(soup)
            elif url.find('crossincode') != -1:
                tmp_proxies = get_proxies_from_crossincode(soup)
            else:
                logger.error('无法从%s获取代理列表' % url)
                tmp_proxies = []
            proxies.extend(tmp_proxies)
            logger.info('从%s成功获取到%s个代理' % (url, str(len(tmp_proxies))))
        except:
            logger.debug('发生未知异常：' + traceback.format_exc())
    logger.info('执行去重后，共成功获取了%s个代理' % str(len(list(set(proxies)))))
    return list(set(proxies))


def get_proxies_from_xicidaili(soup):
    # url = 'https://www.xicidaili.com/'
    proxies = []
    trs = soup.find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) < 8:
            continue
        if tds[5].string.lower() not in ['http', 'https']:
            continue
        proxies.append((tds[1].string, tds[2].string, tds[5].string.lower()))
    return proxies


def get_proxies_from_xiladaili(soup):
    # url = 'http://www.xiladaili.com/'
    proxies = []
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
    return proxies


def get_proxies_from_crossincode(soup):
    # url = 'https://lab.crossincode.com/proxy/'
    proxies = []
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
    return proxies


def main():
    # 豆瓣
    # expect = '大明王朝1566'
    # url = 'https://movie.douban.com/subject/2210001/'

    # 知乎
    expect = '书籍推荐'
    url = 'https://www.zhihu.com/question/22818974'

    # 获取代理列表
    proxy_urls = [
        'https://www.xicidaili.com/',
        'http://www.xiladaili.com/',
        'https://lab.crossincode.com/proxy/',
    ]
    proxies = get_proxies(proxy_urls)
    # 检测代理有效性，似乎可以直接使用http检测，telnet检测没有多大帮助
    start = int(time.time())
    results = []
    for (ip, port, protocol) in proxies:
        proxy = Proxy(ip, port, protocol)
        telnet_result = ''
        telnet_result = proxy.telnet_check(max_check_times=1, timeout=3)
        http_result = ''
        if telnet_result:
            http_result = proxy.http_check(expect, url, max_check_times=1, timeout=3)
        logger.info('代理：%s  telnet检查结果：%s  http检查结果：%s' % (proxy.format(), telnet_result, http_result))
        if http_result:
            results.append("'" + proxy.format() + "',")
    end = int(time.time())
    logger.info('本次检测耗时%s秒' % str(end - start))
    for result in results:
        print(result)


def test():
    # 代理
    proxy = 'http://59.38.61.227:9797'

    # 豆瓣
    # expect = '大明王朝1566'
    # url = 'https://movie.douban.com/subject/2210001/'

    # 知乎
    expect = '书籍推荐'
    url = 'https://www.zhihu.com/question/22818974'

    result = urlparse(url)
    headers['Host'] = result.netloc
    headers['Referer'] = result.scheme + '://' + result.netloc + '/'
    proxies = {
        'http': proxy,
        'https': proxy,
    }
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=3)
        if response.text.find(expect) != -1:
            logger.info('检测成功 检测成功 检测成功')
        else:
            logger.info('查找失败！HTTP响应内容为：\n' + response.text)
            logger.info('检测失败 检测失败 检测失败')
    except:
        logger.info('发生未知异常：' + traceback.format_exc())


if __name__ == '__main__':
    # main()
    test()
