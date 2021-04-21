#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: geofftong
# Mail: geofftong@tencent.com

import argparse
import os
import re

import pymongo
import sys
import time
from bs4 import BeautifulSoup

sys.setrecursionlimit(50000000)


def parse_html(html):
    """
    extracting content from off-line html
    :param html: compressed html document
    :return: context of html document
    """
    soup = BeautifulSoup(html, "lxml")
    [script.extract() for script in soup.findAll('script')]
    [style.extract() for style in soup.findAll('style')]
    reg = re.compile("<[^>]*>")
    text = reg.sub('', soup.prettify())
    text = " ".join(text.replace("\n", "").split())
    return text


def static_cat(output_data):
    """
       computing label's distribution
       :param output_data: output path
       :return:
       """
    host = "mongodb://10.180.67.14:27017,10.57.83.93:27017,100.97.5.73:27017/?replicaSet=rs0"
    client = pymongo.MongoClient(host, unicode_decode_error_handler='ignore')
    db = client.mp
    print(db.docs, db.docs.find().count())
    # result = db.docs.distinct("cat_news")
    print(db.docs.find({"cat_news": {"$exists": True}, "imp_minute": {"$exists": True}}).count())
    # static sizes of all types
    with open(output_data, "w", encoding="utf8") as fw:
        cursor = db.docs.aggregate(
            [
                {"$project": {"cat_news": 1}},
                {"$group": {"_id": "$cat_news", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ]
        )
        for document in cursor:
            fw.write(str(document) + " \n")


def conn_mongo(domains, output):
    """
    fetching data from mongo database
    output data format: id \t time \t cat \t cat_score \t sub_cat \t sub_cat_score \t title \t content \n
    :param output: output file path
    :return:
    """
    host = "mongodb://10.180.67.14:27017,10.57.83.93:27017,100.97.5.73:27017/?replicaSet=rs0"
    client = pymongo.MongoClient(host, unicode_decode_error_handler='ignore')
    db = client.mp
    print(db.docs, db.docs.find().count())
    # result = db.docs.distinct("cat")

    with open(output, "w", encoding="utf8", errors='ignore') as fw:
        # fetch last 5,000,000 labeled data
        for document in db.docs.find(
                {"cat_news": {"$exists": True}, "imp_minute": {"$exists": True}}).sort([("imp_minute", -1)]).limit(5000000):
            id = document["_id"]
            title = document["title"]
            cat = document["cat_news"]
            cat_score = document["cat_news_score"]
            sub_cat = document["subcat_news"]
            sub_cat_score = document["subcat_news_score"]
            time = document["imp_minute"]
            content = parse_html(document["content"].encode("utf8"))
            # filter invalid data in database
            if cat not in domains:
                continue
            fw.write(id + "\t" + time + "\t" + cat + "\t" + str(cat_score) + "\t" + sub_cat + "\t" + str(
                sub_cat_score) + "\t" + title + "\t" + content + "\n")
    return


def split_data(domains, raw_data, max_out_cnt=500000):
    """
     splitting raw data to in-domain's data and out-domain's data
    :param domains: all domains table
    :param raw_data: raw news data
    :return:
    """
    for did in domains:
        out_dom_cnt = 0
        domain_name = domains[did]
        if not os.path.exists("data/raw/%s" % domain_name):
            os.system("mkdir data/raw/%s" % domain_name)
        if not os.path.exists("data/dict/%s" % domain_name):
            os.system("mkdir data/dict/%s" % domain_name)
        with open(raw_data, encoding="utf8") as f:
            in_path = "data/raw/%s/%s_news_tab.txt" % (domain_name, domain_name)
            out_path = "data/raw/%s/non_%s_news_tab.txt" % (domain_name, domain_name)
            with open(in_path, "w", encoding="utf8") as fw_in:
                with open(out_path, "w", encoding="utf8") as fw_out:
                    for idx, line in enumerate(f):
                        tokens = line.strip().split("\t")
                        if len(tokens) != 8:
                            # print("content is null！")
                            continue
                        nid, tim, cat, cat_socre, sub_cat, sub_cat_socre, title, content = tokens
                        if cat == did:
                            fw_in.write(title + "\t" + content + "\n")
                        else:
                            out_dom_cnt += 1
                            if out_dom_cnt > max_out_cnt:
                                continue
                            fw_out.write(title + "\t" + content + "\n")
    return


if __name__ == '__main__':
    start = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', help='raw data file', default="data/news.week.dat")
    args = parser.parse_args()

    # domains hash
    domains_dict = {"体育": "sports", "科技互联网": "tech", "金融财经": "finance", "娱乐": "entertain", "社会民生": "nation",
                    "军事": "military", "国际要闻": "internation", "汽车": "car", "房产": "estate", "旅游": "travel",
                    "游戏": "game", "科学研究": "science", "教育": "education",
                    "数码3C": "digital", "其他": "others"}  # "other"

    # static label's distribution
    # static_cat("data/news.cat.dat")

    # fetch last week's news data: _id \t time \t label \t label_score \t title \t content
    # conn_mongo(domains_dict, args.output)

    # splitting data by domains
    split_data(domains_dict, args.output)  # todo: don't need to read file

    end = time.time()
    print("time: %.3f" % (end - start) + "s")
