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

'''
Modifications has been made to make_suffix_array.py to avoid resource conflict having two processes handling two different parquet files.
    Saving suffix arrays in a sub folder (part of the input file name is used for sub folder name) to avoid
    conflicts in parallel processes on the same node.

    print commands are deleted or replaced with RuntimeError exceptions for unexpected runtime errors.
'''

# Copyright 2021 Google LLC
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import time
import subprocess
import numpy as np
import multiprocessing as mp
from dpk_rep_removal.utils import calculate_timeout
from data_processing.utils import get_logger
logger = get_logger(__name__, level="INFO")

pwd = os.path.dirname(__file__)
dedup_program = f"{pwd}/rust/target/release/dedup_dataset"


# Determine the number of jobs based on the data size (total jobs, and jobs at once)
def determine_job_parameters(data_size):
    if data_size > 10e9:
        return 100, 20
    elif data_size > 1e9:
        return 96, 96
    elif data_size > 10e6:
        return 4, 4
    else:
        return 1, 1


# Run a subprocess command and return the output
def run_subprocess(cmd, timeout=None):
    try:
        if timeout is None:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            stdout, stderr = process.communicate()
        else:
            process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True, timeout=timeout)
            stderr = process.stderr
            stdout = process.stdout

        if process.returncode != 0:
            raise Exception(f"Error in subprocess: {stderr}")
        return stdout
    except Exception as e:
        logger.error(f"Error running command '{cmd}': {e}")
        return None


# Create parts of the dataset
def create_part(data_file, start_byte, end_byte):
    cmd = f"{dedup_program} make-part --data-file {data_file} --start-byte {start_byte} --end-byte {end_byte}"
    logger.info(f"Creating part: {start_byte}-{end_byte}")
    return run_subprocess(cmd)


# Calculate expected size using FACT
def get_expected_size(file_path):
    size_data = os.path.getsize(file_path)
    FACT = np.ceil(np.log(size_data) / np.log(2) / 8)
    return size_data * FACT


# Check the integrity of the files
def check_file_integrity(data_file, started):
    logger.info("Checking file integrity...")
    while True:
        files = [f"{data_file}.part.{s}-{e}" for s, e in started]
        wait = []

        for file, (s, e) in zip(files, started):
            if not os.path.exists(file) or not os.path.exists(f"{file}.table.bin") or os.path.getsize(
                    f"{file}.table.bin") == 0 or get_expected_size(file) != os.path.getsize(file + ".table.bin"):
                logger.warning(f"File missing or invalid: {file}, rerunning.")
                wait.append((s, e))

        if not wait:
            break

        logger.info(f"Re-running {len(wait)} jobs due to failed integrity checks.")
        with mp.Pool(len(wait)) as pool:
            pool.starmap(create_part, [(data_file, s, e) for s, e in wait])

        time.sleep(1)


# Merge the suffix trees
def merge_suffix_trees(files, suffix_array_path, threads, timeout=None):
    cmd = f"{dedup_program} merge --output-file {suffix_array_path} --suffix-path {' --suffix-path '.join(files)} --num-threads {threads}"
    logger.info("Merging suffix trees...")
    result = run_subprocess(cmd, timeout)
    if result:
        logger.info("Merge successful.")
    else:
        logger.error("Merge failed.")
        raise RuntimeError("Merge failed.")


# Cleanup and verification of the final table file

def cleanup_and_verify_final_table(input_file, suffix_array_path, tmp_dir_sub):
    logger.info("Final cleanup and verification...")
    subprocess.run("cat %s.table.bin.* > %s/out.table.bin" % (suffix_array_path, tmp_dir_sub), shell=True)
    subprocess.run("mv %s/out.table.bin %s.table.bin" % (tmp_dir_sub, input_file), shell=True)
    # Verify file integrity
    if os.path.exists(f"{input_file}.table.bin"):
        if os.path.getsize(f"{input_file}.table.bin") % os.path.getsize(input_file) != 0:
            logger.error("File size is incorrect.")
            raise RuntimeError("File size is incorrect.")
    else:
        logger.error("Failed to create the table file.")
        raise RuntimeError("Failed to create the table file.")


def make_suffix_array(input, tmp_dir_sub, dedup_level, num_threads, num_cpus):
    HACK = 100000
    data_size = os.path.getsize(input)
    total_jobs, jobs_at_once = determine_job_parameters(data_size)
    chunk_size = data_size // total_jobs
    started = []
    logger.info(f"Starting the deduplication process for file: {input}")

    timeout = calculate_timeout(data_size, cpu_cores=num_cpus)
    logger.info(f"timeout is: {timeout}")

    # Create dataset parts in parallel
    for jobstart in range(0, total_jobs, jobs_at_once):
        wait = []
        for i in range(jobstart, jobstart + jobs_at_once):
            start_byte, end_byte = i * chunk_size, min((i + 1) * chunk_size + HACK, data_size)
            started.append((start_byte, end_byte))
            wait.append((start_byte, end_byte))

        logger.info(f"Scheduling {jobs_at_once} jobs to create dataset parts.")
        with mp.Pool(jobs_at_once) as pool:
            pool.starmap(create_part, [(input, s, e) for s, e in wait])

    # Check the integrity of all created parts
    check_file_integrity(input, started)

    # Merging the parts into the final dataset
    suffix_array_path = os.path.join(tmp_dir_sub, dedup_level)
    files = [f"{input}.part.{s}-{e}" for s, e in started]
    merge_suffix_trees(files, suffix_array_path, num_threads, timeout)

    # Final cleanup and verification
    cleanup_and_verify_final_table(input, suffix_array_path, tmp_dir_sub)

    logger.info("Deduplication process completed successfully.")
