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
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import pyarrow as pa
from jinja2 import Environment, FileSystemLoader
from plotly.io import to_html


base_constructs = ["uast_package_list", "programming_language", "concepts"]


class Plot:
    """
    Plot class implements the generation of frequency distribution plots of the various components of the profiler report.
    Given a pyarrow table and a column name, it generates the corresponding plot.
    """

    def __init__(self, table, column_name):
        self.table = table
        self.column_name = column_name
        self.column_data = self._get_column_data()

    def _get_column_data(self):
        column_data = self.table[self.column_name].to_numpy()
        split_data = []
        for value in column_data:
            if isinstance(value, str) and "," in value:
                split_data.extend(value.split(","))
            else:
                split_data.append(value)
        return np.array([item.strip() if isinstance(item, str) else item for item in split_data])

    def generate_distribution_plot(self):
        data = self.column_data
        fig = go.Figure()
        cleaned_data = [item for item in data if item is not None]
        fig.add_trace(
            go.Histogram(
                x=cleaned_data,
                nbinsx=len(np.unique(cleaned_data)),
                opacity=0.7,
                marker=dict(color="blue", line=dict(width=1, color="black")),
            )
        )
        # fig.add_trace(go.Histogram(x=data, nbinsx=len(np.unique(data)), opacity=0.7, marker=dict(color='blue', line=dict(width=1, color='black'))))
        fig.update_layout(
            width=500,
            height=300,
            title=dict(text=f"Distribution of {self.column_name}", font=dict(size=14)),
            xaxis=dict(title="Value", title_font=dict(size=12), tickfont=dict(size=10)),
            yaxis=dict(title="Frequency", title_font=dict(size=12), tickfont=dict(size=10)),
            bargap=0.1,
        )
        return to_html(fig, full_html=False)


class Report:
    """
    Generates the report containing the distribution of various syntactic and semantic components.
    """

    def __init__(self, template_file: str):
        path = Path(template_file)
        directory = path.parent
        file_name = path.name
        self.env = Environment(loader=FileSystemLoader(directory))
        self.template = self.env.get_template(file_name)
        self.data = {}
        self.data["title"] = "Profiler Report"
        self.data["heading"] = "Syntactic and Semantic Profile"
        self.data["description"] = "This report presents the detailed profiling report of the input dataset."

    def add_metric(self, metric_id, name, value_counts, graph_html=None):
        if "metrics" not in self.data:
            self.data["metrics"] = []
        self.data["metrics"].append(
            {
                "id": metric_id,
                "name": name,
                "graph_html": graph_html,
                "value_counts": value_counts,
            }
        )

    def render(self):
        return self.template.render(self.data)

    def save(self, output_file):
        output = self.render()
        with open(output_file, "w") as f:
            f.write(output)
        print(f"HTML file generated: {output_file}")

    def get_unique_filename(self, base_path):
        """
        Checks if a file exists and appends a suffix (_1, _2, etc.) to make the filename unique.
        """
        suffix = 1
        new_path = base_path
        while new_path.exists():
            new_path = base_path.with_stem(f"{base_path.stem}_{suffix}")
            suffix += 1
        return new_path

    def sort_value_counts(self, value_counts):
        """
        Sorts a dictionary by its values in descending order.
        """
        return dict(sorted(value_counts.items(), key=lambda x: x[1], reverse=True))

    def recursive_sort_by_value_counts(self, obj):
        """
        Recursively sorts value_counts dictionaries inside the metrics list.
        """
        if isinstance(obj, list):
            # Recurse into each item of the list
            return [self.recursive_sort_by_value_counts(item) for item in obj]
        elif isinstance(obj, dict):
            # Sort 'value_counts' if present
            if "value_counts" in obj and isinstance(obj["value_counts"], dict):
                obj["value_counts"] = self.sort_value_counts(obj["value_counts"])
            # Recurse into dictionary values
            return {k: self.recursive_sort_by_value_counts(v) for k, v in obj.items()}
        else:
            # Return the object as is if it's not a list or dict
            return obj

    def save_as_json(self, output_file):
        # Convert output_file to a Path object
        output_path = Path(output_file)

        # Check if the file already exists and get a unique filename if needed
        unique_output_path = self.get_unique_filename(output_path)

        # Remove non-serializable data, like HTML, if necessary
        serializable_data = self.data.copy()
        for metric in serializable_data.get("metrics", []):
            if "graph_html" in metric:
                del metric["graph_html"]  # Remove or replace with raw data if necessary

        sorted_data = self.recursive_sort_by_value_counts(serializable_data)

        # Save the report data as JSON
        with open(unique_output_path, "w") as json_file:
            json.dump(sorted_data, json_file, indent=4)
        print(f"Report data saved as JSON: {unique_output_path}")


def generate_report(table: pa.Table, metrics_list):
    """
    Generates the profiler report given the table name and the metrics list given as input by the user.
    """
    columns = base_constructs + metrics_list
    script_dir = Path(__file__).parent.resolve()

    # Generate unique suffix using hostname and timestamp
    host_name = socket.gethostname()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]  # Truncate to milliseconds
    unique_suffix = f"{host_name}_{timestamp}"

    # Define file names with the unique suffix
    template_file = str(script_dir / "template.html")
    output_html = str(script_dir / f"output_{unique_suffix}.html")
    output_json = str(script_dir / f"output_{unique_suffix}.json")

    report = Report(template_file)
    id = 0
    for column_name in columns:
        plot = Plot(table, column_name)
        plot_html = plot.generate_distribution_plot()
        # Filter column data to exclude empty keys before counting
        filtered_column_data = [item for item in plot.column_data if item != ""]
        value_counts = dict(Counter(filtered_column_data))
        report.add_metric(id, column_name, value_counts, plot_html)
        id += 1
    report.save(output_html)
    report.save_as_json(output_json)
