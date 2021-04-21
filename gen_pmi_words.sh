#!/usr/bin/env bash
## Author: geofftong
## Processing steps

domains=(tech sports finance entertain nation military internation car estate travel digital game science education others)
word2phrase=libs/word2phrase
th_pmi_0=800 # 1000
th_pmi_1=1000 # 1600

for domain_name in ${domains[@]};
do
    domain_data="data/raw/${domain_name}/${domain_name}_news_tab.txt"
    pmi_data="data/raw/${domain_name}/${domain_name}_pmi.char"
    pmi_dict="data/dict/${domain_name}/${domain_name}.pmi.dict"

    # Step1. preprocessing the data to the char or word format
    echo ">>> Preprocessing the raw data..."
    python utils/utils.py -split_char --data_file $domain_data --char_output $pmi_data

    # Step2. generating ngrams by pmi model
    echo ">>> Training pmi on news domain: ${domain_name}..."                     
    time $word2phrase -train ${pmi_data} -output ${pmi_data}.phrase0 -threshold $th_pmi_0 -debug 2
    time $word2phrase -train ${pmi_data}.phrase0 -output ${pmi_data}.phrase1 -threshold $th_pmi_1 -debug 2
    
    # Step3. extracting and sorting the new words
    echo ">>> Generating sorted ngrams on $domain_name"
    grep -P '([^ ]+[a-zA-Z_]){1,5}[^ ]+' -o ${pmi_data}.phrase1 > tmp.phrases
    python utils/utils.py -format_word --dict_file tmp.phrases
    sort tmp.phrases | uniq -c | sort -r | sed -e 's/^ *//' -e 's/_//g' | awk -F' ' 'BEGIN{OFS="\t"}{if($1 > 10) print $2, $1}' | sort -rt $'\t' -k 2,2 -V | awk -F"\t" '{print $1}' > ${pmi_dict}

    # Step4. validating the new words by search engine like baidu etc.
    # python utils/utils.py -search_filter --dict_file ${pmi_dict}
done

rm tmp.phrases
