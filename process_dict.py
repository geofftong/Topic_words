#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: geofftong
# Mail: geofftong@tencent.com

import pickle
import argparse
import re


def gen_tree(dict_file):
    """
    using words to generate a trie tree
    :param dict_file: words path
    :return: a trie tree
    """
    entity_trie_tree = {}
    with open(dict_file, 'r', encoding='utf8') as f:
        print('constructing tree from %s ...' % dict_file)
        for line in f:
            word = line.strip()
            if word:
                sub_tree = entity_trie_tree
                for e in word:
                    sub_tree.setdefault(e, {})
                    sub_tree = sub_tree[e]
                sub_tree.setdefault('\n', "entity flag")
    print('tree constructing finished.')
    return entity_trie_tree


def clean_dict(dict_path, black_list_path):
    """
    cleaning dictionary with regex, blacklist and search engine
    :param dict_path: dictionary path
    :param black_list_path: blacklist path
    :return:
    """
    new_dict = set()
    with open(black_list_path, encoding="utf8") as f:
        black_list = [line.strip() for line in f]

    # expand dict item to foreign name: xxx-xxx, xxx·xxx
    with open(dict_path, encoding="utf8") as f:
        for idx, line in enumerate(f):
            item = line.strip()
            new_dict.add(item)
            if "·" in item:  # foreign name
                for sub_item in item.split("·"):
                    new_dict.add(sub_item)
                new_dict.add(item.replace("·", "-"))
            if "-" in item:
                for sub_item in item.split("-"):
                    new_dict.add(sub_item)
                new_dict.add(item.replace("-", "·"))

    # filter words contains special punctuation or start/end with some normal punctuation
    unused_punc = '!"#$%&*./;<>@[\\]^_`{|}~。；；;【】>][￥』」「★☆！？~“”《》<>()（）\'‘’．,、～＋●▲／=+］—:'
    used_punc = '-\'’，、.·：'
    with open(dict_path, "w", encoding="utf8") as fw:  # gb18030
        for item in new_dict:
            flag = True
            for punc in unused_punc:
                if punc in item:
                    flag = False
                    break
            for punc in used_punc:
                if item.startswith(punc) or item.endswith(punc):
                    flag = False
                    break

            # filter word contains number, but recall word start with character,like ak47, g20
            if bool(re.search('[0-9]', item)):
                if not re.match("^[a-zA-Z][a-zA-Z0-9]*$", item):
                    continue

            # todo: filter word contains both chinese and english, but remains 'C罗' etc.
            if bool(re.search('[a-zA-Z]', item)):
                if re.compile(u'[\u4e00-\u9fff]').search(item) and len(item) > 2:
                    continue

            # filter bad cases in blacklist
            if item in black_list:
                continue

            # filter single chinese word
            if flag and len(item) > 1:
                fw.write(item + "\n")  # todo: item.lower()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dict_file', help='dict file', default="data/dict/merge.dict")
    parser.add_argument('--black_list', help='black list file', default="data/dict/blacklist")
    parser.add_argument('--dict_output', help='output file', default="data/dict/merge.dict.pkl")
    args = parser.parse_args()

    print("cleaning dict...")
    clean_dict(args.dict_file, args.black_list)

    print("saving dict...")
    trieTree = gen_tree(args.dict_file)
    with open(args.dict_output, 'wb') as fo:
        pickle.dump(trieTree, fo)

