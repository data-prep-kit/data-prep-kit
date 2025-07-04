# HTML to Parquet Transform

---

## Description

This transform iterates through zipped collections of HTML files or single HTML files and generates Parquet files containing the extracted content, leveraging the [Trafilatura library](https://trafilatura.readthedocs.io/en/latest/usage-python.html) for extraction of text, tables, images, and other components.

---

## Contributors

- Sungeun An (sungeun.an@ibm.com)
- Syed Zawad (szawad@ibm.com)

---

## Date

**Last updated:** 10/16/24  
**Update details:** Enhanced table and image extraction features by adding the corresponding Trafilatura parameters.

---

## Input and Output

### Input
- Accepted Formats: Single HTML files or zipped collections of HTML files.  
- Sample Input Files: [sample html files](test-data/input) 

### Output
- Format: Parquet files with the following structure:

```jsonc
{
    "title": "string",             // the member filename
    "document": "string",          // the base of the source archive
    "contents": "string",          // the content of the HTML
    "document_id": "string",      // the document id, a hash of `contents`
    "size": "string",             // the size of `contents`
    "date_acquired": "date",      // the date when the transform was executing
}
```


## Parameters

### User-Configurable Parameters

The table below provides the parameters that users can adjust to control the behavior of the extraction:

| Parameter         | Default    | Description                                                                 |
|-------------------|------------|-----------------------------------------------------------------------------|
| `output_format`    | `markdown` | Specifies the format of the extracted content. Options: `markdown`, `txt`, `json`.  |
| `favor_precision`  | `True`     | Prefers less content but more accurate extraction. Options: `True`, `False`. |
| `favor_recall`     | `True`     | Extracts more content when uncertain. Options: `True`, `False`.              |

### Default Parameters

The table below provides the parameters that are enabled by default to ensure a comprehensive extraction process:

| Parameter           | Default   | Description                                                                 |
|---------------------|-----------|-----------------------------------------------------------------------------|
| `include_tables`     | `True`    | Extracts content from HTML `<table>` elements.                               |
| `include_images`     | `True`    | Extracts image references (experimental feature).                            |
| `include_links`      | `True`    | Extracts hyperlinks from the HTML content.                                   |
| `include_formatting` | `True`    | Preserves basic HTML formatting (e.g., bold, italic) in the extracted content.|

*Note: If both `favor_precision` and `favor_recall` are set to `True`, `favor_recall` takes precedence.*

- To set the output format to plain text, use `output_format='txt'`.
- To prioritize extracting more content over accuracy, set `favor_recall=True` and `favor_precision=False`.
- When invoking the CLI, use the following syntax for these parameters: `--html2parquet_<parameter_name>`. For example: `--html2parquet_output_format='markdown'`.


## Example

### Sample Notebook

See the [sample notebook](html2parquet.ipynb) for an example.


### Sample HTML 
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample HTML File</title>
</head>
<body>
    <h1>Welcome to My Sample HTML Page</h1>
    <h2>Overview</h2>
    <p>This page contains various HTML components to demonstrate structure and formatting.</p>
    <p>This paragraph contains <a href="https://example.com">a link to Example.com</a>.</p>

    <h2>Sample Image</h2>
    <img src="https://via.placeholder.com/300" alt="Placeholder Image" />

    <h2>Key Features</h2>
    <ul>
        <li>Easy to use</li>
        <li>Highly customizable</li>
        <li>Supports multiple components</li>
    </ul>

    <h2>Sample Data Table</h2>
    <table border="1">
        <tr>
            <th>Name</th>
            <th>Age</th>
            <th>City</th>
        </tr>
        <tr>
            <td>Alice</td>
            <td>30</td>
            <td>New York</td>
        </tr>
        <tr>
            <td>Bob</td>
            <td>25</td>
            <td>Los Angeles</td>
        </tr>
        <tr>
            <td>Charlie</td>
            <td>35</td>
            <td>Chicago</td>
        </tr>
    </table>

    <h2>Contact Us</h2>
    <form action="/submit" method="POST">
        <label for="name">Name:</label>
        <input type="text" id="name" name="name" required><br><br>
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" required><br><br>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
```

### Sample Output (Using Default Parameters)

```

# Welcome to My Sample HTML Page

## Overview

This page contains various HTML components to demonstrate structure and formatting.

This paragraph contains [a link to Example.com](https://example.com).

## Sample Image


## Key Features

- Easy to use
- Highly customizable
- Supports multiple components

## Getting Started

- Download the HTML file
- Open it in your browser
- Explore the content

## Sample Data Table

Name |
Age |
City |

Alice |
30 |
New York |

Bob |
25 |
Los Angeles |

Charlie |
35 |
Chicago |


## Contact Us
```

## Usage

### Command-Line Interface (CLI)

Run the transform with the following command:

```
python ./dpk_html2parquet/transform_python.py \
  --data_local_config "{'input_folder': './test-data/input', 'output_folder': './test-data/expected'}" \
  --data_files_to_use '[".html", ".zip"]'
```

- When invoking the CLI, use the following syntax for these parameters: `--html2parquet_<parameter_name>`. For example: `--html2parquet_output_format='markdown'`.



## Further Resources

- [Trafilatura](https://trafilatura.readthedocs.io/en/latest/usage-python.html).
# html2parquet Ray Transform 

This module implements the ray version of the [html2parquet transform](./dpk_html2parquet/ray/).

The HTML conversion is using the [Trafilatura](https://trafilatura.readthedocs.io/en/latest/usage-python.html).

## Prometheus metrics

The transform will produce the following statsd metrics:

| metric name                      | Description                                                      |
|----------------------------------|------------------------------------------------------------------|
| worker_html_doc_count             | Number of HTML documents converted by the worker                  |
| worker_html_pages_count           | Number of HTML pages converted by the worker                      |
| worker_html_page_avg_convert_time | Average time for converting a single HTML page on each worker     |
| worker_html_convert_time          | Time spent converting a single document                           |
