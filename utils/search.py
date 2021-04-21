# -*- coding:utf-8 -*-
# Author: geofftong, luoyi
# Mail: geofftong@tencent.com

import requests
from lxml import etree


"""
================================================
 Extract text from the result of BaiDu search
================================================
"""


def download_html(keywords):
    """
    downloading html
    """
    # https://www.baidu.com/s?wd=testRequest
    key = {'wd': keywords}
    # request Header
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0 cb) like Gecko'}
    proxies = {
        "http": "http://web-proxy.tencent.com:8080",
        "https": "http://web-proxy.tencent.com:8080",
    }
    web_content = requests.get("https://www.baidu.com/s?", params=key, headers=headers, proxies=proxies, timeout=4)
    return web_content.text


def html_parser(html):
    """
    parsing html
    """
    # path_cn = "//div[@id='content_left']//h3[@class='t']>a/text()"
    # path_cn = "//div[@id='content_left']//div[@class='c-span18 c-span-last']"
    # path_cn = "//div[@id='content_left']//div[@class='c-row']//em"
    path_cn = "//div[@id='content_left']//em"
    tree = etree.HTML(html)
    results_cn = tree.xpath(path_cn)
    text_cn = [str(line.xpath('string(.)')).strip() for line in results_cn]
    return text_cn


def search(keyword):
    """
    searching keywords
    """
    em_dict = dict()
    content = download_html(keyword)
    raw_text = html_parser(content)
    for item in raw_text:
        if item in em_dict:
            em_dict[item] += 1
        else:
            em_dict[item] = 1
    sorted_list = sorted(em_dict.items(), key=lambda d: d[1], reverse=True)
    return sorted_list


if __name__ == "__main__":
    result = search("林氏木")  # 猩便
    print(result, result[0][0])
