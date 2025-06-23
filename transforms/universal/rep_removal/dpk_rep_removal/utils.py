# SPDX-License-Identifier: Apache-2.0
# (C) Copyright IBM Corp. 2024.
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

sys_path = "/home/ray/anaconda3/lib/python3.11/site-packages"
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)  # run in OCP

import os
import shutil
import pandas as pd
import GPUtil
import psutil
from transformers import GPT2Tokenizer

tokenizer_name = os.path.abspath(os.path.join(os.path.dirname(__file__), "gpt2"))

try:
    tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_name)
except:
    tokenizer_name = "gpt2"
    tokenizer = GPT2Tokenizer.from_pretrained(tokenizer_name)


def print_file(file_name):
    """
        printing the doc_file lines
        and the length of the doc_file
    """
    content = " "
    with open(file_name, 'r') as f:
        for line in f:
            print(line)
            content += line
    return len(content), content


def decode(x):
    """
    Decode the input bytes with a pre_defined tokenizer "default: gpt2 tokenizer" and output the decoded string.
    - Input param: The input in byte
    - Output: The corresponding string after decoding.
    """

    tokens = np.frombuffer(x, dtype=np.uint8).view(np.uint16).tolist()
    out = tokenizer.decode(tokens)
    return out


def tokenizer_encode(input):
    """
    Tokenize and encode the input string with a pre_defined tokenizer "default: gpt2 tokenizer" and output the corresponding bytes
    - Input param: The input string
    - Output: The corresponding bytes of the tokenized input.
    """
    encoded = tokenizer.encode(input)
    encoded = np.array(encoded, dtype=np.uint16).view(np.uint8).tobytes()
    return encoded


def removeDir(folder):
    """
    Remove a folder including all files and subdirs inside it.
    Input param:
    - folder: The input folder path
    """
    if os.path.exists(folder):
        shutil.rmtree(folder)
    return


def removeFiles(folder):
    """
    Remove files and subdirs inside a given folder.
    Input param:
    -folder: The input folder path
    """

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
    return


def makeDir(folder):
    """
    Make a directory.
    Input param:
    -folder: The input folder path
    """
    if not os.path.exists(folder):
        os.mkdir(folder)


def load_data(original_text_string, input, arg_tokenize):
    if arg_tokenize:  ### if arg_tokenize is True tokenize the input doc strings first
        encoded_input = tokenizer_encode(original_text_string)
        with open(input, 'wb') as fin:
            fin.write(encoded_input)
    else:
        with open(input, 'w') as fin:
            fin.write(original_text_string)


def out_data(output):
    """
        Return the output document content
            Params:
                - output document
    """
    with open(output, 'r') as f:
        repetition_removed_text = f.read()
    return repetition_removed_text


def finish_tokenized(input_tokenized, repeated_subs, output):
    """
        Remove the repeated substrings and save the output doc after repetition removal
            Params:
                - input_tokenized: The tokenized input doc
                - repeated_subs: Repeated substrings found for removal
            - Output: the generated output doc after repetition removal
    """
    with open(input_tokenized, 'rb') as f:
        input_ds = f.read()
    # decode_bytes = decode(input_ds)

    with open(output, "w+") as output_ds:

        ##### All repeated sequences start and end indices
        removed = []
        with open(repeated_subs) as fin:
            for line in fin:
                if 'out' in line: break
            for line in fin:
                removed.append(list(map(int, line.split())))
            removed = removed[::-1]

            start = 0
            if len(removed) == 0:
                out = decode(input_ds)
                output_ds.write(out)
            else:
                while len(removed) > 0:
                    a, b = removed.pop()
                    if a % 2:
                        a = a - 1
                    if b % 2:
                        b = b + 1

                    line = input_ds[start:a]
                    line = decode(line)

                    output_ds.write(line)
                    start = b


def finish_untokenized(input, repeated_subs, output):
    """
        Remove the repeated substrings and save the output doc after repetition removal
            Params:
                - input: The input doc
                - repeated_subs: Repeated substrings found for removal
            - Output: the generated output doc after repetition removal
    """
    with open(input, 'rb') as f:
        input_ds = f.read()

    with open(output, "w+") as output_ds:

        ##### All repeated sequences start and end indices
        removed = []
        with open(repeated_subs) as fin:
            for line in fin:
                if 'out' in line: break
            for line in fin:
                removed.append(list(map(int, line.split())))
            removed = removed[::-1]

            start = 0
            if len(removed) == 0:
                out = input_ds
                output_ds.write(out)
            else:
                while len(removed) > 0:
                    a, b = removed.pop()
                    if a % 2:
                        a = a - 1
                    if b % 2:
                        b = b + 1

                    line = input_ds[start:a]

                    output_ds.write(line)
                    start = b


def print_docs_pq(inp_pq, out_pq):
    """
    The function `print_docs_pq` reads two Parquet files, `inp_pq` and `out_pq`, and prints the
    contents of all documents, from each file along with some additional information.

    :param inp_pq: The `inp_pq` parameter is the file path to the input Parquet file. This file contains
    the original documents
    :param out_pq: The `out_pq` parameter is the file path to the output parquet file. It is used to
    read the generated documents from the parquet file
    """

    df_inp = pd.read_parquet(inp_pq)
    df_out = pd.read_parquet(out_pq)
    num_row = df_inp.shape[0]

    for i in range(df_inp.shape[0]):
        len_original_doc = len(df_inp.loc[i, 'contents'])
        len_generated_doc = len(df_out.loc[i, 'contents'])
        print(f"\n###################################### Doc number {i} #####################################")
        print(
            f"################## Original doc with length in chars {len_original_doc}: \n {df_inp.loc[i, 'contents']} \n")
        print(
            f"################## Generated doc with length in chars {len_generated_doc}: \n {df_out.loc[i, 'contents']} \n")

    print(
        f"#################################### Total number of row in the parquet file is: {num_row} #################################### \n")
    print(
        f"############################################################################################################################### \n")


def print_doc_pq_row(inp_pq, out_pq, row_idx):
    """
    The function `print_docs_pq_row` reads two Parquet files, `inp_pq` and `out_pq`, and prints the
    contents of a specific row, `row_idx`, from each file along with some additional information.

    :param inp_pq: The `inp_pq` parameter is the file path to the input Parquet file. This file contains
    the original documents
    :param out_pq: The `out_pq` parameter is the file path to the output parquet file. It is used to
    read the generated documents from the parquet file
    :param row_idx: The `row_idx` parameter is the index of the row in the Parquet file that you want to
    print the documents for. It is used to access the specific row in both the input and output Parquet
    files
    """

    df_inp = pd.read_parquet(inp_pq)
    df_out = pd.read_parquet(out_pq)
    num_row = df_inp.shape[0]

    len_original_doc = len(df_inp.loc[row_idx, 'contents'])
    len_generated_doc = len(df_out.loc[row_idx, 'contents'])
    print(f"\n###################################### Doc number {row_idx} #####################################")
    print(
        f"################## Original doc with length in chars {len_original_doc}: \n {df_inp.loc[row_idx, 'contents']} \n")
    print(
        f"################## Generated doc with length in chars {len_generated_doc}: \n {df_out.loc[row_idx, 'contents']} \n")
    print(
        f"#################################### Total number of row in the parquet file is: {num_row} #################################### \n")
    print(
        f"############################################################################################################################### \n")

def get_cpu_speed():
    """
    Get the current CPU speed
    :return: CPU speed in MHz
    """
    return psutil.cpu_freq().current

def get_gpu_usage_and_speed():
    gpus = GPUtil.getGPUs()
    if not gpus:
        return 0, 0

    gpu = gpus[0] #assuming we're interested in the first GPU
    gpu_usage = gpu.memoryUtil # memory usage percentage (0 to 1)
    gpu_speed = gpu.clock

    return gpu_usage, gpu_speed

def calculate_timeout(file_size, cpu_cores=None, buffer_time=60):
    """
    Calculate the timeout for subprocess.run() based on system performance and file size

    :param file_size: the file size in bytes to be processed
    :param num_threads: number of threads being used by the task
    :param buffer_time: buffer time to add to the timeout (default 5 seconds)
    """
    if cpu_cores is None:
        cpu_cores = psutil.cpu_count(logical=False)
    cpu_speed = get_cpu_speed()
    print(f"cpu speed: {cpu_speed} MHz, Cores: {cpu_cores}")

    gpu_usage, gpu_speed = get_gpu_usage_and_speed()
    print(f"gpu_usage: {gpu_usage * 100:.2f}%, GPU speed: {gpu_speed} MHz")

    #calculate the cpu throughput in MB/sec (rough estimate)
    # we assume that cpu throughput is proportional to CPU speed and number of cores
    cpu_throughput = cpu_speed * cpu_cores

    #timeout = (file_size / (cpu_throughput * num_threads)) + (gpu_usage * gpu_speed) + buffer_time
    timeout = (file_size / cpu_throughput) + (gpu_usage * gpu_speed) + buffer_time

    return timeout
