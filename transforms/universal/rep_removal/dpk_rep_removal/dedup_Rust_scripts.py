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

import subprocess
import os
pwd = os.path.dirname(__file__)
toml_path = f"{pwd}/rust/Cargo.toml"

def find_repeated_substrings(input, length_thresh, cache_dir, num_threads, frequency_threshold, retain_first_copy):
    ### Finding all repeated substrings within a document
    ### Identifying all substrings of a given length that are repeated more than some threshold number of times
    ### --frequency-threshold: number of times that substrings of a given length are repeated (default value: 1)
    ### --length-threshold: The length threshold is dataset-dependent (50 tokens used in the paper).
    try:
        if retain_first_copy:
            find_repetition_cmd = ['cargo', 'run',
                                   '--manifest-path', toml_path,
                                   '--',
                                   'self-similar',
                                   '--data-file', input,
                                   '--length-threshold', length_thresh,
                                   '--cache-dir', cache_dir,
                                   '--num-threads', num_threads,
                                   '--frequency-threshold', frequency_threshold,
                                   '--retain-first-copy']
            subprocess.run(find_repetition_cmd)
        else:
            find_repetition_cmd = ['cargo', 'run',
                                   '--manifest-path', toml_path,
                                   '--',
                                   'self-similar',
                                   '--data-file', input,
                                   '--length-threshold', length_thresh,
                                   '--cache-dir', cache_dir,
                                   '--num-threads', num_threads,
                                   '--frequency-threshold', frequency_threshold]
            subprocess.run(find_repetition_cmd)

    except subprocess.CalledProcessError:
        raise RuntimeError("error during subprocess call. skipping file")



def collect_duplicates(input, length_thresh, cache_dir, repeated_pairs_file):
    ### Collecting the duplicates together
    ### Finding string sequences that should be removed from the document
    try:
        collect_cmd = ['cargo', 'run',
                       '--manifest-path', toml_path,
                       '--',
                       'collect',
                       '--data-file', input,
                       '--cache-dir', cache_dir,
                       '--length-threshold', length_thresh]
        with open(repeated_pairs_file, 'w') as removal_file:
            subprocess.run(collect_cmd, stdout=removal_file)

    except subprocess.CalledProcessError:
        raise RuntimeError("error during subprocess call. skipping file")


def collect_duplicates_avoidIO(input, length_thresh, cache_dir):
    ### Collecting the duplicates together
    ### Finding string sequences that should be removed from the document

    ### List to store subprocess outputs to pass to other functions
    ### repeated_pairs_list is a list not a file to avoid I/O
    repeated_pairs_list = []
    try:
        collect_cmd = ['cargo', 'run',
                       '--manifest-path', toml_path,
                       '--',
                       'collect',
                       '--data-file', input,
                       '--cache-dir', cache_dir,
                       '--length-threshold', length_thresh]

        # Run the subprocess command and capture the output
        result = subprocess.run(collect_cmd, capture_output=True, text=True)

        # Append the output to the list
        result_stdout = result.stdout
        repeated_pairs_list = result_stdout.split('\n')

        # print ('#########################################################################################################')
        # print ('#########################################################################################################')
        # print ('#########################################################################################################', repeated_pairs_list)

        return repeated_pairs_list

    except subprocess.CalledProcessError:
        raise RuntimeError("error during subprocess call. skipping file")
