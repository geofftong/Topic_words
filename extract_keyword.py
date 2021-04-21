# -*- coding: utf-8 -*-
# Author: geofftong
# Mail: geofftong@tencent.com

import argparse
import math
import re
import jieba.posseg as pseg


def edit_distance(str1, str2):
    """
    computing edit distance between two string
    :param str1: string a
    :param str2: string b
    :return: edit distance
    """
    len_str1 = len(str1) + 1
    len_str2 = len(str2) + 1
    # create matrix
    matrix = [0 for n in range(len_str1 * len_str2)]
    # init x axis
    for i in range(len_str1):
        matrix[i] = i
    # init y axis
    for j in range(0, len(matrix), len_str1):
        if j % len_str1 == 0:
            matrix[j] = j // len_str1
    for i in range(1, len_str1):
        for j in range(1, len_str2):
            if str1[i - 1] == str2[j - 1]:
                cost = 0
            else:
                cost = 1
            matrix[j * len_str1 + i] = min(matrix[(j - 1) * len_str1 + i] + 1,
                                           matrix[j * len_str1 + (i - 1)] + 1,
                                           matrix[(j - 1) * len_str1 + (i - 1)] + cost)
    # print(str1, str2, matrix[-1])
    return matrix[-1]


def coverage(keyword_sorted_list):
    """
    using coverage distance to filter keywords: 伊格达拉 vs 伊戈达拉, 科比布莱恩特 vs 科比 etc.
    :param keyword_sorted_list: sorted candidate keywords
    :return: filtered sorted candidate keywords
    """
    keywords_pool = dict()
    cand_name_set = set()
    for word, score in keyword_sorted_list:
        filter_flag = False
        if "-" in word or "·" in word:
            for name_token in re.split('[-·]', word):
                if name_token in cand_name_set:
                    filter_flag = True
                for existed_word in cand_name_set:  # key
                    if edit_distance(name_token, existed_word) < 2:
                        filter_flag = True
                cand_name_set.add(name_token)
        else:
            for existed_word in cand_name_set:
                if word in existed_word or existed_word in word or edit_distance(word, existed_word) < 2:  # 足球 vs 世界足球
                    filter_flag = True
        if not filter_flag:
            cand_name_set.add(word)
            keywords_pool[word] = score
    return sorted(keywords_pool.items(), key=lambda d: d[1], reverse=True)


def pos_filter(content, keywords_list):
    """
    using pos tag to filter keywords: 竟然, 跳跃 etc.
    :param content: source document
    :param keywords_list: sorted candidate keywords
    :return:filtered sorted candidate keywords and pos tag table
    """
    pos_tag_tabel = dict()
    pos_filter_list = list()
    words = pseg.cut(content)
    for word, flag in words:
        # print('%s, %s' % (word, flag))
        if word not in pos_tag_tabel:
            pos_tag_tabel[word] = flag
    for word, score in keywords_list:
        if word in pos_tag_tabel:
            # print(word, pos_tag_tabel[word])
            unused_tag = {'a', 'v', 't', 'm', 'd', 'f', 'i', 'q', 'r'}  # todo
            if pos_tag_tabel[word] in unused_tag:
                continue
        pos_filter_list.append((word, score))
    return pos_filter_list, pos_tag_tabel


def match_keywords(raw_news_path, idf_dict_path, recg_result, output_file, threshhold=28000, top_k=10, sample=100):
    """
    matching keywords form news data with tf-idf, lda, coverage, pos tag filter etc.
    :param raw_news_path: raw news data
    :param idf_dict_path: idf dictionary
    :param recg_result: masked document
    :param output_file: keywords output file
    :param threshhold: threshhold of count of keywords dictionary
    :param top_k: top k candidate keywords
    :param sample: sample data to analysis
    :return: predicted keywords list
    """
    idf_dict = dict()
    raw_news = list()
    doc_num = 0
    predict_result = list()
    with open(raw_news_path, encoding='utf8') as f:
        for idx, line in enumerate(f):
            if idx <= sample:
                tokens = line.strip().split("\t")
                raw_news.append(tokens[0] + "\n" + "".join(tokens[1:]))
            doc_num = idx + 1
        print("doc num: ", doc_num)
    with open(idf_dict_path, encoding='utf8') as f:
        for idx, line in enumerate(f):
            if idx > threshhold:  # high precision
                break
            tokens = line.strip().split("\t")
            idf_dict[tokens[0]] = float(tokens[2])  # idf：[2]
    with open(output_file + ".filter." + str(threshhold), "w", encoding='utf8') as fw:
        with open(recg_result, encoding='utf8') as f:
            for idx, line in enumerate(f):
                if idx >= sample:  # test 100 news for analyzing
                    break
                tf_dict, score_dict = dict(), dict()
                tokens = line.strip().split("\t")
                for word in tokens:
                    if word not in tf_dict:
                        tf_dict[word] = 1
                    else:
                        tf_dict[word] += 1
                for word in tf_dict:
                    if word not in idf_dict:
                        continue
                    score_dict[word] = tf_dict[word] * math.log(doc_num / (1 + idf_dict[word]))
                sorted_list = sorted(score_dict.items(), key=lambda d: d[1], reverse=True)  # reverse=True
                sorted_list = coverage(sorted_list)
                sorted_list, pos_table = pos_filter(raw_news[idx].split("\n")[1], sorted_list[:top_k])
                fw.write(str(idx + 1) + "." + raw_news[idx] + "\n")
                for item in sorted_list:  # [:top_k]
                    if item[0] in pos_table:
                        fw.write(item[0] + "\t" + str(item[1]) + "\t" + pos_table[item[0]] + "\t" + str(idf_dict[item[0]]) + "\n")
                    else:
                        fw.write(item[0] + "\t" + str(item[1]) + "\t" + "TBD" + "\t" + str(idf_dict[item[0]]) + "\n")
                fw.write("\n")
                predict_result.append(sorted_list)
    return predict_result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain_data', help='domain data',
                        default="data/raw/sports_news/sports_news_tab.txt")
    parser.add_argument('--out_domain_data', help='out domain data',
                        default=".data/raw/sports_news/non_sports_news_tab.txt")
    parser.add_argument('--dict_file', help='dict file', default="../../data/dict/merge.dict.pkl")

    parser.add_argument('--domain_output', help='domain recognize file',
                        default="data/dict/merge.domain.mask")
    parser.add_argument('--out_domain_output', help='others recognize file',
                        default="data/dict/merge.out_domain.mask")
    parser.add_argument('--rank_dict', help='rank dict file',
                        default="data/dict/merge.dict.rank")  # tf-idf
    parser.add_argument('--keyword_file', help='keywords output file',
                        default="data/dict/merge.dict.keywords")
    args = parser.parse_args()
    args.domain_output = args.domain_data[:-3] + "mask"
    args.out_domain_output = args.out_domain_data[:-3] + "mask"

    print("matching keywords...")
    match_keywords(args.domain_data, args.rank_dict, args.domain_output, args.keyword_file)
    print("done.")
