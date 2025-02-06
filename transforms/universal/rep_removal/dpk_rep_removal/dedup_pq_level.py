# (C) Copyright IBM Corp. 2025.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import sys
import numpy as np

######################### Only modification ###########################
######################### Comment out for DEBUGGING ###################################
# sys_path = "/home/ray/anaconda3/lib/python3.11/site-packages"
# if sys_path not in sys.path:
#     sys.path.insert(0, sys_path)  # run in OCP

import os
import multiprocessing as mp
import pandas as pd
import struct
from collections import defaultdict
import dpk_rep_removal.utils
import transformers
from transformers import GPT2Tokenizer

run_in_OCP = True

#### Save the tokenizer in a local path to speed up the process
#### Get tokenizer from the local path to speed up the process


tokenizer_name = os.path.abspath(os.path.join(os.path.dirname(__file__), "gpt2"))
tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_name)
transformers.utils.logging.set_verbosity_error()  ##disable the warnings


def read_pq_files(input_pq_list):
    pq_df = pd.read_parquet(input_pq_list)
    return pq_df


UID = 0


def sep():
    pre_sep = b"\xff\xff"
    post_sep = b""

    global UID
    UID += 1
    return pre_sep + struct.pack("<I", UID) + post_sep


def encode(x):
    if args_tokenize:
        out = tokenizer.encode(x)
        out = np.array(out, dtype=np.uint16).view(np.uint8).tobytes()
    else:
        out = x.encode("utf-8")
    return out


def decode(x):
    """
    Decode the input bytes with a pre_defined tokenizer "default: gpt2 tokenizer" and output the decoded string.
    - Input param: The input in byte
    - Output: The corresponding string after decoding.
    """

    tokens = np.frombuffer(x, dtype=np.uint8).view(np.uint16).tolist()
    out = tokenizer.decode(tokens)
    return out


def load_pq_docs(pq_df, content_col, save_dir, dataset_name, tokenize, num_threads):
    global args_tokenize
    args_tokenize = tokenize

    pre_sep = b"\xff\xff"
    post_sep = b""

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    fout = open(os.path.join(save_dir, dataset_name), "wb")

    with mp.get_context("fork").Pool(num_threads) as p:
        sizes = [0]
        docs_content_text = pq_df[content_col].tolist()
        encoded_docs = p.map(encode, docs_content_text)

        for doc in encoded_docs:
            next_line = sep() + doc
            fout.write(next_line)
            sizes.append(sizes[-1] + len(next_line))
    fout.close()
    open(os.path.join(save_dir, dataset_name + ".size"), "wb").write(np.array(sizes, dtype=np.uint64).tobytes())


def load_pq_docs_once(pq_df, content_col, save_dir, dataset_name, tokenize, num_threads):
    global encoded_docs, loaded_size, args_tokenize
    args_tokenize = tokenize

    pre_sep = b"\xff\xff"
    post_sep = b""

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    fout = open(os.path.join(save_dir, dataset_name), "wb")

    with mp.get_context("fork").Pool(num_threads) as p:
        loaded_size = [0]
        docs_content_text = pq_df[content_col].tolist()
        encoded_docs = p.map(encode, docs_content_text)

        for doc in encoded_docs:
            next_line = sep() + doc
            fout.write(next_line)
            loaded_size.append(loaded_size[-1] + len(next_line))
    fout.close()
    open(os.path.join(save_dir, dataset_name + ".size"), "wb").write(np.array(loaded_size, dtype=np.uint64).tobytes())
    ### To avoid tokenizing again we pass the tokenized column to use later
    # return enc_text, loaded_size


def load_pq_docs_once_avoidIO(pq_df, content_col, save_dir, dataset_name, tokenize, num_threads):
    global args_tokenize, encoded_docs, loaded_size
    args_tokenize = tokenize

    pre_sep = b"\xff\xff"
    post_sep = b""

    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    fout = open(os.path.join(save_dir, dataset_name), "wb")

    with mp.get_context("fork").Pool(num_threads) as p:
        loaded_size = [0]
        docs_content_text = pq_df[content_col].tolist()
        encoded_docs = p.map(encode, docs_content_text)

        for doc in encoded_docs:
            next_line = sep() + doc
            fout.write(next_line)
            loaded_size.append(loaded_size[-1] + len(next_line))
    fout.close()

    ### Avoid writing to file to speed up the process
    # open(os.path.join(save_dir,dataset_name+".size"), "wb").write(np.array(sizes,dtype=np.uint64).tobytes())
    ### To avoid tokenizing again we pass the tokenized column to use later
    # return enc_text, loaded_size


def gen_output_doc(args):
    global remove_ex, args_tokenize

    this_idx, row = args

    if this_idx in remove_ex:
        if args_tokenize:
            row = encode(row)
            for start, end in remove_ex[this_idx][::-1]:
                if start % 2:
                    start = start - 1
                if end % 2:
                    end = end + 1
                # print(start,end)
                # end = int(end-6)
                # print(start,end)
                row = row[:start] + row[end:]
            row = decode(row)
        else:
            for start, end in remove_ex[this_idx][::-1]:
                # print(start,end)
                row = row[:start] + row[end:]
    return row


def gen_output_doc_once(args):
    global remove_ex, args_tokenize, encoded_docs

    this_idx, row = args

    if this_idx in remove_ex:
        if args_tokenize:
            row = encoded_docs[this_idx]
            for start, end in remove_ex[this_idx][::-1]:
                if start % 2:
                    start = start - 1
                if end % 2:
                    end = end + 1
                # print(start,end)
                # end = int(end-6)
                # print(start,end)
                row = row[:start] + row[end:]
            row = decode(row)
        else:
            for start, end in remove_ex[this_idx][::-1]:
                # print(start,end)
                row = row[:start] + row[end:]
    return row


def save_deduped_pq(pq_df, output_dir, content_col, num_threads, tokenize):
    global args_tokenize, remove_ex
    args_tokenize = tokenize

    # pq_df = pd.read_parquet(input_pq_list)
    pre_content_col_size = sum(pq_df[content_col].str.len())

    ### Removing the repeated subsequences from all parquet docs
    docs = [(i, row) for i, row in enumerate(pq_df[content_col])]
    p = mp.get_context("fork").Pool(int(num_threads))
    docs = p.map(gen_output_doc, docs)

    pq_df[content_col] = docs
    deduped_content_col_size = sum(pq_df[content_col].str.len())

    #### saving the output parquet file once
    pq_df.to_parquet(output_dir)

    return pre_content_col_size, deduped_content_col_size


def save_deduped_pq_once(pq_df, output_dir, content_col, num_threads, tokenize):
    global args_tokenize, remove_ex
    args_tokenize = tokenize

    # pq_df = pd.read_parquet(input_pq_list)
    pre_content_col_size = sum(pq_df[content_col].str.len())

    ### Removing the repeated subsequences from all parquet docs
    docs = [(i, row) for i, row in enumerate(pq_df[content_col])]

    p = mp.get_context("fork").Pool(int(num_threads))
    docs = p.map(gen_output_doc_once, docs)

    pq_df[content_col] = docs
    deduped_content_col_size = sum(pq_df[content_col].str.len())

    #### saving the output parquet file once
    pq_df.to_parquet(output_dir)

    return pre_content_col_size, deduped_content_col_size


def extract_dup_per_doc(size_file, repeated_pairs):
    global remove_ex
    remove = []
    fin = open(repeated_pairs)
    for line in fin:
        if 'out' in line: break
    for line in fin:
        remove.append(list(map(int, line.split())))

    sizes = np.frombuffer(open(size_file, "rb").read(), dtype=np.uint64)

    remove_ex = defaultdict(list)

    # count_between_docs = 0
    # duplicate_between_docs = []       ### for printing and investigation
    ptr = 0
    for i, byte_start in enumerate(sizes[:-1]):
        byte_end = sizes[i + 1]
        # print(byte_start, byte_end, remove[ptr])
        while ptr < len(remove) and byte_start <= remove[ptr][0] < byte_end:
            # print(remove[ptr])

            ##### if a duplicate is made from two subsequent documents,
            ##### Do not remove it as each part might be the only occurrence in its related doc
            ##### This follows our strategy to retain the first occurrence of each duplicate
            if remove[ptr][1] > byte_end + 6:
                # count_between_docs += 1
                # duplicate_between_docs.append(i)   ### for printing and investigation
                ptr += 1
                continue  ### Do not remove this duplicate

            # The magic value 6 here corresponds to the 4-byte index prefix followed by \xff\xff.
            remove_ex[i].append((max(int(remove[ptr][0] - byte_start - 6), 0),
                                 int(min(int(remove[ptr][1] - byte_start),
                                         byte_end - byte_start)) - 6))  ################## added -6 to exclude sep
            ptr += 1
    # print ('############# Number of duplicate made from two subsequent documents: ', count_between_docs)
    # print ('############# Number of duplicate made from two subsequent documents: ', duplicate_between_docs)

    # df_dict = pd.DataFrame(remove_ex)
    # print(remove_ex)
    # return remove_ex


def extract_dup_per_doc_avoidIO(repeated_pairs):
    global remove_ex, loaded_size
    remove = []
    fin = open(repeated_pairs)
    for line in fin:
        if 'out' in line: break
    for line in fin:
        remove.append(list(map(int, line.split())))

    ### Avoid I/O process for .size file to speed up the process
    # sizes = np.frombuffer(open(size_file, "rb").read(), dtype=np.uint64)
    sizes = loaded_size

    remove_ex = defaultdict(list)

    # count_between_docs = 0
    # duplicate_between_docs = []     ### for printing and investigation
    ptr = 0
    for i, byte_start in enumerate(sizes[:-1]):
        byte_end = sizes[i + 1]
        # print(byte_start, byte_end, remove[ptr])
        while ptr < len(remove) and byte_start <= remove[ptr][0] < byte_end:
            # print(remove[ptr])

            ##### if a duplicate is made from two subsequent documents,
            ##### Do not remove it as each part might be the only occurrence in its related doc
            ##### This follows our strategy to retain the first occurrence of each duplicate
            if remove[ptr][1] > byte_end + 6:
                # count_between_docs += 1
                # duplicate_between_docs.append(i)   ### for printing and investigation
                ptr += 1
                continue  ### Do not remove this duplicate

            # The magic value 6 here corresponds to the 4-byte index prefix followed by \xff\xff.
            remove_ex[i].append((max(int(remove[ptr][0] - byte_start - 6), 0),
                                 int(min(int(remove[ptr][1] - byte_start),
                                         byte_end - byte_start)) - 6))  ################## added -6 to exclude sep
            ptr += 1
    # print ('############# Number of duplicate made from two subsequent documents: ', count_between_docs)
    # print ('############# Number of duplicate made from two subsequent documents: ', duplicate_between_docs)

    # df_dict = pd.DataFrame(remove_ex)
    # print(remove_ex)
    # return remove_ex


def extract_dup_per_doc_avoidIO_further(repeated_pairs):
    global remove_ex, loaded_size
    remove = []

    #### Avoid I/O process for repeated_pairs_file to speed up the process
    #### repeated_pairs is a list passed to the function not a file to avoid I/O
    # fin = open(repeated_pairs)
    # for line in fin:
    #     if 'out' in line: break
    # for line in fin:
    #     remove.append(list(map(int,line.split())))

    i = 0
    while 'out' not in repeated_pairs[i]:
        # print (repeated_pairs[i])
        i += 1
    i += 1
    while i < len(repeated_pairs):
        # print (repeated_pairs[i])
        remove.append(list(map(int, repeated_pairs[i].split())))
        i += 1

    remove = remove[:-1]
    # print (remove)

    ### Avoid I/O process for .size file to speed up the process
    # sizes = np.frombuffer(open(size_file, "rb").read(), dtype=np.uint64)
    sizes = loaded_size

    remove_ex = defaultdict(list)

    # count_between_docs = 0
    # duplicate_between_docs = []     ### for printing and investigation
    ptr = 0
    for i, byte_start in enumerate(sizes[:-1]):
        byte_end = sizes[i + 1]
        # print(byte_start, byte_end, remove[ptr])
        while ptr < len(remove) and byte_start <= remove[ptr][0] < byte_end:
            # print(remove[ptr])

            ##### if a duplicate is made from two subsequent documents,
            ##### Do not remove it as each part might be the only occurrence in its related doc
            ##### This follows our strategy to retain the first occurrence of each duplicate
            if remove[ptr][1] > byte_end + 6:
                # count_between_docs += 1
                # duplicate_between_docs.append(i)   ### for printing and investigation
                ptr += 1
                continue  ### Do not remove this duplicate

            # The magic value 6 here corresponds to the 4-byte index prefix followed by \xff\xff.
            remove_ex[i].append((max(int(remove[ptr][0] - byte_start - 6), 0),
                                 int(min(int(remove[ptr][1] - byte_start),
                                         byte_end - byte_start)) - 6))  ################## added -6 to exclude sep
            ptr += 1
    # print ('############# Number of duplicate made from two subsequent documents: ', count_between_docs)
    # print ('############# Number of duplicate made from two subsequent documents: ', duplicate_between_docs)

    # df_dict = pd.DataFrame(remove_ex)
    # print(remove_ex)
    # return remove_ex