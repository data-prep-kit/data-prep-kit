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
import glob
import json
from collections import Counter, defaultdict
from json.decoder import JSONDecodeError
from pathlib import Path


def aggregate_metrics(input_dir, output_file):
    # Initialize a dictionary to hold aggregated counts
    aggregated_metrics = defaultdict(lambda: defaultdict(int))

    # Loop through each JSON file in the specified directory
    for json_file in glob.glob(f"{input_dir}/output_*.json"):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                for metric in data.get("metrics", []):
                    metric_name = metric["name"]
                    value_counts = metric.get("value_counts", {})

                    # Aggregate counts for each unique metric
                    for key, count in value_counts.items():
                        aggregated_metrics[metric_name][key] += count
        except JSONDecodeError:
            print(f"Skipping invalid JSON file: {json_file}")
    # Prepare the final output structure
    aggregated_data = {
        "title": "Aggregated Profiler Report",
        "heading": "Aggregated Syntactic and Semantic Profile",
        "description": "This report presents aggregated profiling data across multiple JSON files.",
        "metrics": [],
    }

    # Convert aggregated metrics to the required format
    for metric_name, value_counts in aggregated_metrics.items():
        aggregated_data["metrics"].append({"name": metric_name, "value_counts": dict(value_counts)})

    # Write the aggregated results to the output JSON file
    with open(output_file, "w") as f:
        json.dump(aggregated_data, f, indent=4)

    print(f"Aggregated report saved as: {output_file}")


# Usage example
aggregate_metrics(input_dir="../", output_file="aggregated_output.json")
