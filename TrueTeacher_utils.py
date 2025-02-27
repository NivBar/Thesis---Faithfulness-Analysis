import sys
from pyserini.search import FaissSearcher
from transformers import T5ForConditionalGeneration
from transformers import T5Tokenizer
import torch
import pandas as pd
import json
from tqdm import tqdm
import os
import pickle
import numpy as np
import re
from transformers import DPRQuestionEncoderTokenizer
import warnings
from transformers import AutoTokenizer
from pyserini.search.lucene import LuceneSearcher
import paramiko
from scp import SCPClient
import pickle
import io
import socket
import tempfile

warnings.filterwarnings("ignore")

embedding_model = 'intfloat/e5-base'
# rel_round = 5
rel_round = "LTR"

index_path = f"/lv_local/home/niv.b/llama/pyserini_output_tommy_{rel_round}_max"
# faiss_tokenizer = AutoTokenizer.from_pretrained(embedding_model)
faiss_searcher = FaissSearcher(index_path, embedding_model)
lucene_searcher = LuceneSearcher(index_path + "_sparse")

data_dict = {}
with open(index_path + f"/tommy_data_{rel_round}_max.jsonl", 'r') as file:
    for line in file:
        # Parse each line as a JSON object
        entry = json.loads(line)
        # Use 'id' as the key and 'contents' as the value
        try:
            data_dict[entry['id']] = entry['contents']
        except:
            data_dict[entry['id']] = entry['text']

names_otn = {key: key.replace('ROUND-', '').replace('00', '0') + '-creator' for key in data_dict.keys()}

names_nto = {v: k for k, v in names_otn.items()}

model_path = 'google/t5_11b_trueteacher_and_anli'
tokenizer = T5Tokenizer.from_pretrained(model_path)

model_run = True

if model_run:
    model = T5ForConditionalGeneration.from_pretrained(model_path, device_map="auto")
    model.eval()
else:
    model = "model"

cache_file = 'cache_offline.pkl'
cache_usage = 0


def init_model():
    model_path = 'google/t5_11b_trueteacher_and_anli'
    tokenizer = T5Tokenizer.from_pretrained(model_path)
    model = T5ForConditionalGeneration.from_pretrained(model_path, device_map="auto")
    model.eval()
    return tokenizer, model


def trim_complete_sentences(text):
    # Split the text into sentences using a regex pattern
    sentences = re.split(r'(?<=[.!?])\s+|\n', text)

    # Check if the last sentence is incomplete and remove it if necessary
    if sentences and sentences[-1].strip() and sentences[-1].strip()[-1] not in ['.', '!', '?']:
        sentences.pop()

    word_count = sum(len(sentence.split()) for sentence in sentences)
    if word_count <= 150:
        truncated_text = ' '.join(sentences)
        return truncated_text

    # Check if truncation is necessary
    if sentences:
        word_count = sum(len(sentence.split()) for sentence in sentences)
        truncated_text = " ".join(sentences)

        while word_count > 150:
            if len(sentences) < 2:
                break
            sentences.pop()
            word_count = sum(len(sentence.split()) for sentence in sentences)
            if word_count <= 150:
                truncated_text = ' '.join(sentences)
                return truncated_text


def create_feature_df(cp, online=False):
    df = pd.read_csv(f'/lv_local/home/niv.b/llama/TT_input/bot_followup_{cp}.csv').astype(str)
    df = df[[col for col in df.columns if col not in ['prompt', 'text']]]

    if cp == 'student':
        df['creator'] = 'creator'

    if online:
        # ROUND-04-124_124_1_T-DG0YZT
        df["previous_docno_str"] = df.apply(
            lambda row: "ROUND-" + str(int(row.round_no) - 1).zfill(2) + "-" + row.docno.split("-", 2)[-1], axis=1)
        return df

    # 02-017-01-creator
    if cp == 'student':
        df["previous_docno_str"] = df.apply(lambda row: str(row.round_no).zfill(2) + "-" + str(
            row.query_id).zfill(3).replace("00", "0") + "-" + str(row.username).zfill(2) + "-creator", axis=1)
    else:
        df["previous_docno_str"] = df.apply(lambda row: str(row.round_no).zfill(2) + "-" + str(
            row.query_id).zfill(3).replace("00", "0") + "-" + str(row.creator).zfill(2) + "-creator", axis=1)
    # 08-02-DYN_1201R2-13
    df['docno'] = df.apply(lambda row: str(int(row.round_no) + 1).zfill(2) + "-" + str(row.query_id).zfill(2) + "-" +
                                       row.username + "-" + str(row.creator), axis=1)
    return df


# def create_jsonl_file():
#     df = pd.read_csv("/lv_local/home/niv.b/llama/greg_data.csv")
#     filename = '/lv_local/home/niv.b/llama/greg_output.jsonl'
#     with open(filename, 'w') as file:
#         for _, row in df.iterrows():
#             json_object = {
#                 "id": row['docno'],
#                 "contents": row['current_document'].replace('\n', ' ').strip() + '\n'
#             }
#             file.write(json.dumps(json_object) + '\n')


# def retrieve_top_docs(query, k=10, round_no=1):
#     global lucene_searcher, faiss_searcher, faiss_tokenizer
#     try:
#         if online:
#             hits = searcher.search(query, k=843)
#             return [hits[i].docid for i in range(843) if int(hits[i].docid.split("-")[1]) < int(round_no)][:k], hits
#         else:
#             hits = searcher.search(query, k=k)
#     except:
#         hits = searcher.search(truncate_to_max_tokens(query, faiss_tokenizer, max_tokens=510), k=k)
#     return [hits[i].docid for i in range(k)], hits

def perform_retrieval(searcher, query, online=False, k=10, round_no=1, max_tokens=510):
    # Perform search (for both FAISS and Lucene searchers)
    query = truncate_to_max_tokens(query, max_tokens)
    if online:
        hits = searcher.search(query, k=843)
        # doc_ids = [hits[i].docid for i in range(843) if int(hits[i].docid.split("-")[1]) < int(round_no)][:k]
        doc_ids = [hits[i].docid for i in range(843) if
                   "_T" not in hits[i].docid and int(hits[i].docid.split("-")[1]) < int(round_no)][:k]

    else:
        hits = searcher.search(query, k=k)
        doc_ids = [hits[i].docid for i in range(k)]

    return doc_ids, hits


# Main function to retrieve top documents using both FAISS (dense) and TFIDF (sparse)
def retrieve_top_docs(query, k=10, round_no=1, online=False):
    global lucene_searcher, faiss_searcher

    # FAISS (dense retrieval using E5 embeddings)
    faiss_doc_ids, faiss_hits = perform_retrieval(
        searcher=faiss_searcher, query=query, online=online, k=k, round_no=round_no
    )

    # Lucene (TFIDF-based sparse retrieval)
    lucene_doc_ids, lucene_hits = perform_retrieval(
        searcher=lucene_searcher, query=query, online=online, k=k, round_no=round_no
    )

    # Return the two independent lists: FAISS (E5) results and TFIDF results
    return faiss_doc_ids, lucene_doc_ids, faiss_hits, lucene_hits


def get_prob_mean(text1, text2):
    return (get_prob_one_sided(text1, text2) + get_prob_one_sided(text2, text1)) / 2


def get_prob_one_sided(premise, hypothesis):
    global tokenizer
    input_ids = tokenizer(
        f'premise: {premise} hypothesis: {hypothesis}',
        return_tensors='pt',
        truncation=True,
        max_length=512).input_ids
    decoder_input_ids = torch.tensor([[tokenizer.pad_token_id]])
    outputs = model(input_ids=input_ids, decoder_input_ids=decoder_input_ids)
    logits = outputs.logits
    probs = torch.softmax(logits[0], dim=-1)
    one_token_id = tokenizer('1').input_ids[0]
    entailment_prob = probs[0, one_token_id].item()
    return entailment_prob


def truncate_to_max_tokens(text, max_tokens=512):
    global tokenizer
    tokens = tokenizer.encode(text, add_special_tokens=True)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        truncated_text = tokenizer.decode(truncated_tokens, clean_up_tokenization_spaces=True)
        return truncated_text
    else:
        return text


def create_CF_ref_dict(df):
    existing = df[df.creator != 'creator'][['query_id', 'creator', 'CF@1_ref']].replace('nan',
                                                                                        np.nan).dropna().drop_duplicates(
        subset=['query_id', 'creator']).reset_index(drop=True)
    return existing.set_index(['query_id', 'creator']).to_dict('index')


def calculate_metrics(top_docs, sentences, cache):
    global cache_usage
    """Calculate the metrics (cf_vals, cf_ref_vals, norm_vals) for a list of top documents using a cache to avoid redundant calls."""
    cf_vals, cf_ref_vals, norm_vals = [], [], []
    for doc in top_docs:
        # Check if this doc's values are already cached
        if doc not in cache:
            cache[doc] = {}

        vals = []
        for sentence in sentences:
            # Check cache for the result before calling get_prob_one_sided
            if sentence not in cache[doc]:
                cache[doc][sentence] = get_prob_one_sided(doc, sentence)
            else:
                cache_usage += 1
            vals.append(cache[doc][sentence])

        bool_vals = [v >= 0.5 for v in vals]
        res = sum(bool_vals) / len(bool_vals)

        # Process reference sentences
        ref_sentences = [sentence.strip() for sentence in re.split(r'[.!?]', doc) if sentence]
        ref_vals = []
        for ref_sentence in ref_sentences:
            if ref_sentence not in cache[doc]:
                cache[doc][ref_sentence] = get_prob_one_sided(doc, ref_sentence)
            ref_vals.append(cache[doc][ref_sentence])

        ref_bool_vals = [v >= 0.5 for v in ref_vals]
        ref_res = sum(ref_bool_vals) / len(ref_bool_vals)

        norm_res = min(res / ref_res if ref_res != 0 else 1.0, 1.0)

        cf_vals.append(res)
        cf_ref_vals.append(ref_res)
        norm_vals.append(norm_res)

    return cf_vals, cf_ref_vals, norm_vals


def store_results(df, idx, metrics, suffix, k, k_half):
    """Store NEF and EF metrics in the DataFrame for both k and k/2."""
    cf_vals, cf_ref_vals, norm_vals = metrics

    # Store k metrics
    df.loc[idx, f'NEF@{k}_{suffix}'] = sum(norm_vals) / len(norm_vals)
    df.loc[idx, f'NEF@{k}_max_{suffix}'] = max(norm_vals)
    df.loc[idx, f'EF@{k}_{suffix}'] = sum(cf_vals) / len(cf_vals)
    df.loc[idx, f'EF@{k}_max_{suffix}'] = max(cf_vals)

    # Store k/2 metrics
    df.loc[idx, f'NEF@{k_half}_{suffix}'] = sum(norm_vals[:k_half]) / len(norm_vals[:k_half])
    df.loc[idx, f'NEF@{k_half}_max_{suffix}'] = max(norm_vals[:k_half])
    df.loc[idx, f'EF@{k_half}_{suffix}'] = sum(cf_vals[:k_half]) / len(cf_vals[:k_half])
    df.loc[idx, f'EF@{k_half}_max_{suffix}'] = max(cf_vals[:k_half])


def process_top_docs(top_docs_docnos, greg_df, sentences, k, cache, online=False):
    """Retrieve documents, truncate them, and calculate metrics while using cache to avoid redundant calculations."""

    top_docs = [
        greg_df[greg_df['docno'] == docno]['current_document'].values[0]
        if not greg_df[greg_df['docno'] == docno].empty
        else None  # Or use a default value, e.g., ''
        for docno in top_docs_docnos
    ]

    # Calculate metrics while using cache to save redundant calls
    return calculate_metrics(top_docs, sentences, cache)


# Function to load or initialize the dictionary
def load_cache():
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
            print(f"Cache loaded from file - {cache_file} (size - {get_cache_size(cache)} bytes)")
    else:
        cache = {}
        print("No pickle file found. Initialized an empty cache.")
    return cache


# Function to save the cache to a pickle file
def save_cache(cache):
    global cache_usage
    with open(cache_file, 'wb') as f:
        pickle.dump(cache, f)
        print(f"cache size changed - {get_cache_size(cache)} bytes")
        print(f"cache used {cache_usage} times!")


def get_cache_size(cache):
    total_size = sys.getsizeof(cache)  # Get size of the top-level dictionary
    for key, value in cache.items():
        total_size += sys.getsizeof(key)  # Add size of each key
        if isinstance(value, dict):
            total_size += get_cache_size(value)  # Recursively add size of nested dictionaries
        else:
            total_size += sys.getsizeof(value)  # Add size of non-dict values
    return total_size
