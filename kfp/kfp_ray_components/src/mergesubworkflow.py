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
import json
import subprocess

from runtime_utils import KFPUtils



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start merge sub workflow")
    parser.add_argument("--prefix", type=str)
    parser.add_argument("--params", type=str, default=None)
    parser.add_argument("--merge_folder1", type=str, nargs='?', const='', default=None)
    parser.add_argument("--merge_folder2", type=str, nargs='?', const='', default=None)
    parser.add_argument("--merge_folder3", type=str, nargs='?', const='', default=None)
    parser.add_argument("--merge_folder4", type=str, nargs='?', const='', default=None)
    parser.add_argument("--merge_folder5", type=str, nargs='?', const='', default=None)


    args, unknown_args = parser.parse_known_args()
    merge_folders = []
    if args.merge_folder1 is not None and args.merge_folder1 != "":
        merge_folders.append(args.merge_folder1)
    if args.merge_folder2 is not None and args.merge_folder2 != "":
        merge_folders.append(args.merge_folder2)
    if args.merge_folder3 is not None and args.merge_folder3 != "":
        merge_folders.append(args.merge_folder3)
    if args.merge_folder4 is not None and args.merge_folder4 != "":
        merge_folders.append(args.merge_folder4)
    if args.merge_folder5 is not None and args.merge_folder5 != "":
        merge_folders.append(args.merge_folder5)

    command = ['python', '/pipelines/component/src/subworkflow.py']
    if args.prefix:
        command.extend(["prefix", args.prefix])
    if len(merge_folders) > 0:
        if args.params:
            params = args.params
            params = params.replace('}"', "}")
            params = params.replace('"{', "{")
            dic = KFPUtils.load_from_json(params)
            dic[args.prefix + 'merge_input_dirs'] = ",".join(merge_folders)
            command.extend(['--params', json.dumps(dic)])
    command.extend(unknown_args)
    print(command)
    # Execute the merge sub process
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)