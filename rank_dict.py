#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: geofftong, changyumiao
# Mail: geofftong@tencent.com

import pickle
import argparse
import math


def recg_entity(data_file, dict_file, output_file, max_match=1000000):
    """
    converting source documents to masked dict-items
    :param data_file: source documents
    :param dict_file: dictionary
    :param output_file: masked text data
    :param max_match: max number of matching lines
    :return:
    """
    with open(dict_file, 'rb') as f:
        dic = pickle.load(f)
    with open(data_file, 'r', encoding='utf8') as f:
        with open(output_file, 'w', encoding='utf8') as fw:
            for idx, line in enumerate(f):
                if idx > max_match:
                    break
                if (idx + 1) % 10000 == 0:
                    print("processed:", idx + 1)
                tokens = line.strip().split("\t")
                title, content = tokens[0], "".join(tokens[1:])
                content = title + content
                start, n = 0, len(content)
                entities = []
                while start < n:
                    end = None
                    sub_tree = dic
                    matching_flag = 1
                    for idx in range(start, n):
                        if '\n' in sub_tree:  # update longest entity (entity_type) when matching
                            end = idx
                        if content[idx] in sub_tree:  # continue matching
                            sub_tree = sub_tree[content[idx]]
                        else:  # mismatch
                            matching_flag = 0
                            break
                    if matching_flag and '\n' in sub_tree:  # still in matching when end of line
                        end = n
                    if end:
                        entities.append((start, end))
                        start = end  # todo: overlap
                    else:
                        start += 1
                if entities:
                    entities = [content[start:end] for start, end in entities]
                    fw.write('\t'.join(entities) + "\n")


def rank_entity(domain_entity_file, others_entity_file, dict_file):
    """
    ranking candidate dict with domain info (diversity  and popularity)
    :param domain_entity_file: in-domain masked text data
    :param others_entity_file: out-domain masked text data
    :param dict_file: dictionary
    :return:
    """
    score_dict = dict()
    sports_idf_dict, others_idf_dict = dict(), dict()
    domain_num, others_num = 0, 0
    with open(domain_entity_file, encoding='utf8') as f:
        for idx, line in enumerate(f):
            tokens = line.strip().split("\t")
            for word in set(tokens):  # idf
                if word not in sports_idf_dict:
                    sports_idf_dict[word] = 1
                else:
                    sports_idf_dict[word] += 1
            domain_num = idx + 1
    print("domain_num: ", domain_num)
    with open(others_entity_file, encoding='utf8') as f:
        for idx, line in enumerate(f):
            tokens = line.strip().split("\t")
            for word in set(tokens):  # idf
                if word not in others_idf_dict:
                    others_idf_dict[word] = 1
                else:
                    others_idf_dict[word] += 1
            others_num = idx + 1
    print("others_num: ", others_num)
    for word in sports_idf_dict:
        if word in others_idf_dict:  # sub-idf * log df
            score_dict[word] = (math.log(domain_num * 1.0 / (1 + sports_idf_dict[word])) - math.log(
                others_num * 1.0 / (1 + others_idf_dict[word]))) * (math.log(1 + sports_idf_dict[word]))
        else:
            score_dict[word] = (math.log(domain_num * 1.0 / (1 + sports_idf_dict[word])) - math.log(
                others_num * 1.0)) * (math.log(1 + sports_idf_dict[word]))
    # print(len(sports_idf_dict), len(others_idf_dict))
    sorted_list = sorted(score_dict.items(), key=lambda d: d[1])  # reverse=True
    with open(dict_file, "w", encoding='utf8') as fw:
        for item in sorted_list:
            if item[0] in others_idf_dict:
                fw.write(item[0] + "\t" + str(item[1]) + "\t" + str(sports_idf_dict[item[0]]) + "\t" + str(
                    others_idf_dict[item[0]]) + "\n")
            else:
                fw.write(item[0] + "\t" + str(item[1]) + "\t" + str(sports_idf_dict[item[0]]) + "\t" + str(0) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain_data', help='domain data',
                        default="data/raw/sports_news/sports_news_tab.txt")
    parser.add_argument('--out_domain_data', help='out domain data',
                        default="data/raw/sports_news/non_sports_news_tab.txt")
    parser.add_argument('--dict_file', help='dict file', default="../../data/dict/merge.dict.pkl")
    parser.add_argument('--domain_output', help='domain recognize file',
                        default="data/dict/merge.domain.mask")
    parser.add_argument('--out_domain_output', help='others recognize file',
                        default="data/dict/merge.out_domain.mask")
    parser.add_argument('--rank_dict', help='rank dict file',
                        default="data/dict/merge.dict.rank")  # tf-idf

    args = parser.parse_args()
    args.domain_output = args.domain_data[:-3] + "mask"
    args.out_domain_output = args.out_domain_data[:-3] + "mask"

    print("masking domain data...")
    recg_entity(args.domain_data, args.dict_file, args.domain_output)

    print("masking out_domain data...")
    recg_entity(args.out_domain_data, args.dict_file, args.out_domain_output, max_match=500000)

    print("re-ranking dict...")
    rank_entity(args.domain_output, args.out_domain_output, args.rank_dict)
