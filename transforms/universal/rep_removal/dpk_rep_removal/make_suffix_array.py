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

import logging
import os
import time
import subprocess
import numpy as np
from dpk_rep_removal.utils import calculate_timeout

logging.basicConfig(level=logging.DEBUG)


def make_suffix_array(input, tmp_dir_sub, dedup_level, num_threads, num_cpus):
    # data_size = os.path.getsize(sys.argv[1])
    data_size = os.path.getsize(input)

    HACK = 100000

    started = []

    if data_size > 10e9:
        total_jobs = 100
        jobs_at_once = 20
    elif data_size > 1e9:
        total_jobs = 96
        jobs_at_once = 96
    elif data_size > 10e6:
        total_jobs = 4
        jobs_at_once = 4
    else:
        total_jobs = 1
        jobs_at_once = 1

    S = data_size // total_jobs
    timeout = calculate_timeout(data_size, cpu_cores=num_cpus)
    logging.info(f"timeout is: {timeout}")

    pwd = os.path.dirname(__file__)
    dedup_program = f"{pwd}/rust/target/release/dedup_dataset"

    try:
        for jobstart in range(0, total_jobs, jobs_at_once):
            wait = []
            for i in range(jobstart, jobstart + jobs_at_once):
                s, e = i * S, min((i + 1) * S + HACK, data_size)
                # cmd = "./target/debug/dedup_dataset make-part --data-file %s --start-byte %d --end-byte %d"%(sys.argv[1], s, e)

                ###########################################################################################################################################
                # cmd = "./target/debug/dedup_dataset make-part --data-file %s --start-byte %d --end-byte %d"%(input, s, e)
                cmd = f"{dedup_program}" + " make-part --data-file %s --start-byte %d --end-byte %d" % (input, s, e)
                ###########################################################################################################################################

                started.append((s, e))
                #run the command with subprocess and capture the output
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                wait.append(result)

                if e == data_size:
                    break

            #Ensure all commands have finished
            for result in wait:
                if result.returncode != 0:
                    raise RuntimeError(f"Error occurred: {result.stderr}")

        # check the output of part files and rerun if necessary
        while True:
            # files = ["%s.part.%d-%d"%(sys.argv[1],s, e) for s,e in started]
            files = ["%s.part.%d-%d" % (input, s, e) for s, e in started]

            wait = []
            for x, (s, e) in zip(files, started):
                go = False
                if not os.path.exists(x):
                    go = True
                else:
                    size_data = os.path.getsize(x)
                    FACT = np.ceil(np.log(size_data) / np.log(2) / 8)
                    if not os.path.exists(x) or not os.path.exists(x + ".table.bin") or os.path.getsize(
                            x + ".table.bin") == 0 or size_data * FACT != os.path.getsize(x + ".table.bin"):
                        go = True
                if go:
                    # cmd = "./target/debug/dedup_dataset make-part --data-file %s --start-byte %d --end-byte %d"%(sys.argv[1], s, e)
                    ###########################################################################################################################################
                    # cmd = "./target/debug/dedup_dataset make-part --data-file %s --start-byte %d --end-byte %d"%(input, s, e)
                    cmd = f"{dedup_program}" + " make-part --data-file %s --start-byte %d --end-byte %d" % (input, s, e)
                    ###########################################################################################################################################

                    # run the command to recreate the missing or failed parts
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    wait.append(result)
                    if len(wait) >= jobs_at_once:
                        break

            # Ensure all commands have finished
            for result in wait:
                if result.returncode != 0:
                    raise RuntimeError(f"Error occurred: {result.stderr}")

            time.sleep(1)
            # break the loop when no jobs are left
            if len(wait) == 0:
                break

        #os.popen("rm tmp/out.table.bin.*").read()

        torun = " --suffix-path ".join(files)
        # pipe = os.popen("./target/debug/dedup_dataset merge --output-file %s --suffix-path %s --num-threads %d"%("tmp/out.table.bin", torun, num_threads))

        #### Saving suffix arrays in a sub folder (part of the input file name is used for sub folder name)
        #### to avoid conflicts in parallel processes on the same node
        suffix_array_path = os.path.join(tmp_dir_sub, dedup_level)

        ###########################################################################################################################################
        # pipe = os.popen("./target/debug/dedup_dataset merge --output-file %s --suffix-path %s --num-threads %d"%(suffix_array_path, torun,num_threads ))
        cmd = f"{dedup_program}" + " merge --output-file %s --suffix-path %s --num-threads %d" % (
        suffix_array_path, torun, num_threads)
        ###########################################################################################################################################

        # run the merge command:
        logging.info("running the merge")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError("Something went wrong with merging.")

        #### Saving suffix arrays in a sub folder (part of the input file name is used for sub folder name)
        #### to avoid conflicts in parallel processes on the same node
        subprocess.run("cat %s.table.bin.* > %s/out.table.bin" % (suffix_array_path, tmp_dir_sub), shell=True)

        subprocess.run("mv %s/out.table.bin %s.table.bin" % (tmp_dir_sub, input), shell=True)

        logging.info('merging complete')
        # if os.path.exists(sys.argv[1]+".table.bin"):
        if os.path.exists(input + ".table.bin"):
            if os.path.getsize(input + ".table.bin") % os.path.getsize(input) != 0:
                raise RuntimeError("File size is wrong")

        else:
            raise RuntimeError("Failed to create table")

    except subprocess.TimeoutExpired:
        raise RuntimeError("subprocess timed out. skipping file")

    except subprocess.CalledProcessError:
        raise RuntimeError("error during subprocess call. skipping file")
