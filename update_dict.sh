#!/usr/bin/env bash
## Author: geofftong
## Processing steps, updating per day

wiki_dict="data/dict/wiki.dict"
crawl_dict="data/dict/crawl.dict"
user_dict="data/dict/all.user_dict"
domains=(tech sports finance entertain nation military internation car estate travel digital game science education others)  # 15 domains

## Step1. fetching labeled data from mongodb and spliting data by domains
python fetch_data.py --output "data/news.week.dat"

## Step2. generating candidate words pool by metrics like pmi etc.
bash gen_pmi_words.sh

## Step3. do the loop to generate domains dicts
for var in ${domains[@]};
do
    pmi_dict="data/dict/${var}/${var}.pmi.dict"
    merge_dict="data/dict/${var}/${var}.merge.dict"
    domain_data="data/raw/${var}/${var}_news_tab.txt"
    out_domain_data="data/raw/${var}/non_${var}_news_tab.txt"

    # Step3.1. merging all dicts, and generating a trie tree
    cat ${wiki_dict} ${crawl_dict} ${pmi_dict} > ${merge_dict}
    python process_dict.py --dict_file ${merge_dict} --dict_output ${merge_dict}.pkl

    # Step3.2. converting source documents to masked dict-items, and re-ranking candidate dict with domain info
    python rank_dict.py --dict_file ${merge_dict}.pkl --domain_data ${domain_data} --out_domain_data ${out_domain_data} --rank_dict ${merge_dict}.rank

    # Step3.3. updating offline dicts on all domains
    docs_num=`wc -l ${domain_data} | awk '{print $1}'`
    awk -F'\t' -v OFS="\t" '{print $1, $3}' ${merge_dict}.rank > ${merge_dict}.idf.${docs_num}
    awk -F'\t' '{if($2<=-1.84) print $1}' ${merge_dict}.rank | head -10000 > ${merge_dict}.buf

    # Step3.4. extracting keywords based the dict and metrics like tf-idf etc.
    # python extract_keyword.py  --rank_dict ${merge_dict}.rank --domain_data $domain_data --keyword_file ${merge_dict}.keyword
done

# optional: generate user dict for segmentation
awk -F'\t' '{if($2<=-6.66) print $1}' data/dict/*/*.rank > ${user_dict}
