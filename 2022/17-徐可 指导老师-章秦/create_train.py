import argparse
import json
from transformers import AutoTokenizer
from multiprocessing import Pool
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("--qrels_file", type=str, default="../data/mixed/qrels.train.tsv", help="qrels file")
parser.add_argument("--query_file", type=str, default="../data/mixed/train.query.txt", help="query file")
parser.add_argument('--collection_file', type=str, default="../data/mixed/corpus.tsv", help="collections file")
parser.add_argument("--save_to", type=str, default="../data/mixed/train/train.json", help="processd train json file")
parser.add_argument("--tokenizer_name", type=str, default="bert-base-chinese", help="pretrained model tokenizer")
args = parser.parse_args()

def read_queries(queries):
    qmap = {}
    with open(queries, encoding='utf-8') as f: # windows下open函数要指定utf-8编码方式打开文件
        for l in f:
            qid, qry = l.strip().split('\t')
            qmap[qid] = qry
    return qmap # 返回的是一个字典，key是query的id，value是query语句

def read_collections(collections):
    cmap = {}
    with open(collections, encoding='utf-8') as f:
        for l in f:
            seg = l.strip().split('\t')
            if len(seg) == 2:
                did, content = seg
            if len(seg) == 3:
                did, title, text = seg
                content = title + ' ' + text
            cmap[did] = content
    return cmap

def encode_one(line):
    line = line.strip().split("\t")  # query_id, _, doc_id, _
    if not isinstance(line, list) or len(line) < 2:
        return None
    query_id, doc_id = line[0], line[2]
    query = queries[query_id]
    doc = collections[doc_id] 
    spans = [query, doc]
    if not spans[0] or not spans[1]:
        return None
    tokenized = [
        tokenizer(
            s.lower(), 
            add_special_tokens=False, 
            truncation=True,
            max_length=510,
            return_attention_mask=False,
            return_token_type_ids=False,
        )["input_ids"] for s in spans
    ]
    return json.dumps({'spans': tokenized})


tokenizer = AutoTokenizer.from_pretrained(args.tokenizer_name, use_fast=True)
queries = read_queries(args.query_file)
collections = read_collections(args.collection_file)

with open(args.save_to, 'w') as f:
    with Pool() as p:
        all_tokenized = p.imap_unordered(
            encode_one,
            tqdm(open(args.qrels_file), ascii=True, desc=args.qrels_file),
            chunksize=500,
        )
        for x in all_tokenized:
            if x is None:
                continue
            f.write(x + "\n")
