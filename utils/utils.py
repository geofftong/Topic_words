#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: geofftong
# Mail: geofftong@tencent.com

import jieba.posseg as pseg
import re
import argparse
from search import search


# def coverage():
#     return


def search_val(word_path, search_log):
    """
    validating word by search engine, like baidu, google, etc
    :param word_path:
    :return:
    """
    correct_pair = list()
    word_set = set()
    with open(word_path, encoding="utf8") as f:
        for idx, line in enumerate(f):
            if (idx + 1) % 1000 == 0:
                print("processed:", idx + 1)
            word = line.strip()
            result = search(word)
            if len(result) > 0 and result[0][0] != word:
                print(idx, word, result[0][0])
                correct_pair.append(word + "\t" + result[0][0])
                word = result[0][0]
            word_set.add(word)
    with open(word_path, "w", encoding="utf8") as fw:
        for word in word_set:
            fw.write(word + "\n")
    with open(search_log, "w", encoding="utf8") as fw:
        for item in correct_pair:
            fw.write(item + "\n")
    return


def pos_tag(filepath):
    """

    :param filepath:
    :return:
    """
    pos_tabel = dict()
    with open(filepath, encoding="utf8") as f:
        for idx, line in enumerate(f):
            content = line.strip().split("\t")[5]
            words = pseg.cut(content)
            for word, flag in words:
                pos_tabel[word] = flag
    return pos_tabel


def pos_filter(pos_tag_tabel, words_list):
    """

    :param pos_tag_tabel:
    :param words_list:
    :return:
    """
    pos_filter_list = list()
    unused_tag = {'a', 'v', 't', 'm', 'c', 'd', 'f', 'i', 'q', 'r'}  # todo
    for word in words_list:
        if word in pos_tag_tabel:
            # print(word, pos_tag_tabel[word])
            if pos_tag_tabel[word] in unused_tag:
                continue
        pos_filter_list.append((word))
    return pos_filter_list


def split_char_ch_en(raw_data, output):
    """

    :param raw_data:
    :param output:
    :return:
    """
    # string = "China's Legend Holdings will split its business. 该集团总裁朱利安周二表示，中国联想控股将分拆其多个业务部门在股市上市。"
    with open(output, "w", encoding="utf8") as fw:
        with open(raw_data, encoding="utf8") as f:
            for idx, line in enumerate(f):   # title \t content
                result = ""
                line = line.strip().replace("\t", " ")
                for item in line:
                    if ord(item) < 256:
                        result += item
                    else:
                        for char in item:
                            result += " " + char + " "
                fw.write(" ".join(result.split()) + "\n")


def format_word(file_path):
    """

    :param file_path:
    :return:
    """
    formatted_words = list()
    with open(file_path, encoding="utf8", errors='ignore') as f:
        for idx, line in enumerate(f):
            # chinese & english
            if re.compile(u'[\u4e00-\u9fff]').search(line.strip()):
                formatted_words.append(line.strip().replace("_", ""))
            else:  # ak-47 g20
                formatted_words.append(line.strip().replace("_", " "))
    with open(file_path, "w", encoding="utf8") as fw:
        for word in formatted_words:
            fw.write(word + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dict_file', help='dict file', default="data/dict/test_news.txt")
    parser.add_argument('--data_file', help='data file', default="data/dict/merge.dict")
    parser.add_argument('--char_output', help='char format output file', default="data/dict/merge.dict.pkl")
    parser.add_argument('--search_log', help='search log', default="data/dict/search_log")
    parser.add_argument('-format_word', dest='format_flag', help='format word', action='store_true', default=False)
    parser.add_argument('-split_char', dest='split_flag', help='split char', action='store_true', default=False)
    parser.add_argument('-pos_filter', dest='pos_flag', help='pos filter', action='store_true', default=False)
    parser.add_argument('-search_filter', dest='search_flag', help='search filter', action='store_true', default=False)
    args = parser.parse_args()

    if args.format_flag:
        format_word(args.dict_file)

    if args.split_flag:
        split_char_ch_en(args.data_file, args.char_output)

    if args.search_flag:
        search_val(args.dict_file, args.search_log)

    if args.pos_flag:
        # result = pos_filter("李克强总")
        for item in pseg.cut("向带"):
            print(item)
