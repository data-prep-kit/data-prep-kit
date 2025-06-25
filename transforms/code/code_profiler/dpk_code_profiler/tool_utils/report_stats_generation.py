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

import json
import os

import matplotlib.pyplot as plt
import numpy as np


def process_and_save(value_counts, metric_name, output_data):
    # Separate numeric keys, skipping "0"
    numeric_keys = {}

    for k, v in value_counts.items():
        if k == "0":  # Skip the key "0"
            continue
        try:
            numeric_keys[float(k)] = v  # Try converting key to float
        except ValueError:
            continue  # Skip non-numeric keys

    # Sort numeric keys
    keys = np.array(list(numeric_keys.keys()))
    counts = np.array([numeric_keys[key] for key in keys])

    sorted_indices = np.argsort(keys)
    keys = keys[sorted_indices]
    counts = counts[sorted_indices]

    # Calculate PDF
    total_count = np.sum(counts)
    pdf = counts / total_count

    # Calculate CDF
    cdf = np.cumsum(pdf)

    # Save the data points
    output_data[f"value_count_{metric_name}_pdf"] = {str(k): p for k, p in zip(keys, pdf)}
    output_data[f"value_count_{metric_name}_cdf"] = {str(k): c for k, c in zip(keys, cdf)}

    # Plot Distribution, PDF, and CDF
    plt.figure(figsize=(15, 8))

    # Distribution (Bar Plot)
    plt.subplot(3, 1, 1)
    plt.bar(keys, counts, width=0.4, color="skyblue", alpha=0.8)
    plt.title(f"Distribution of {metric_name}")
    plt.xlabel("Values")
    plt.ylabel("Counts")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # PDF (Bar Plot)
    plt.subplot(3, 1, 2)
    plt.bar(keys, pdf, width=0.4, color="blue", alpha=0.7)
    plt.title(f"PDF (Probability Density Function) of {metric_name}")
    plt.xlabel("Values")
    plt.ylabel("Probability")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # CDF (Line Plot)
    plt.subplot(3, 1, 3)
    plt.plot(keys, cdf, marker="o", color="orange", linewidth=2)
    plt.title(f"CDF (Cumulative Distribution Function) of {metric_name}")
    plt.xlabel("Values")
    plt.ylabel("Cumulative Probability")
    plt.grid(axis="y", linestyle="--", alpha=0.7)

    # Save plot as PNG
    plt.tight_layout()
    plt.savefig(f"{metric_name}_distribution.png")
    plt.close()


# Read JSON input
input_file = "aggregated_output.json"  # Adjust path as needed
output_file = "report_stats_generation.json"  # Output JSON file
with open(input_file, "r") as f:
    data = json.load(f)

# Metrics to process
metrics_to_process = {"ccr", "code_snippet_len", "avg_fn_len_in_snippet"}
output_data = {}

# Process and save for selected metrics
for metric in data["metrics"]:
    metric_name = metric["name"]
    if metric_name in metrics_to_process:
        value_counts = metric["value_counts"]
        process_and_save(value_counts, metric_name.lower(), output_data)

# Save processed data to JSON
with open(output_file, "w") as f:
    json.dump(output_data, f, indent=4)

print(f"Processed data points saved to {output_file}")
