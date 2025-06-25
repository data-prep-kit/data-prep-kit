# SPDX-License-Identifier: Apache-2.0
import os
import requests
from humanfriendly import format_size
import pandas as pd
import glob
from urllib.parse import unquote

# from typing import List, Optional

## Reads parquet files in a folder into a pandas dataframe
def read_parquet_files_as_df(parquet_dir: str)  -> pd.DataFrame:
    """
    Reads all parquet files from a directory and combines them into a single pandas DataFrame.

    Args:
        parquet_dir (str): Path to the directory containing parquet files.

    Returns:
        pandas.DataFrame: A concatenated DataFrame containing data from all parquet files.
                         Returns an empty DataFrame if no files are found or all files are empty.

    Example usage:
        df = read_parquet_files_as_df('data/parquet_files/')
    """
    parquet_files = glob.glob(os.path.join(parquet_dir, '*.parquet'))
    if not parquet_files:
        print(f"No parquet files found in {parquet_dir}")
        return pd.DataFrame()

    # read each parquet file into a DataFrame and store in a list
    dfs: list[pd.DataFrame] = []
    for file in parquet_files:
        try:
            df: pd.DataFrame = pd.read_parquet(file)
            if not df.empty:
                dfs.append(df)
        except Exception as e:
            print(f"Error reading {file}: {str(e)}")

    # Concatenate all DataFrames into a single DataFrame
    if dfs:
        data_df: pd.DataFrame = pd.concat(dfs, ignore_index=True)
        print(f"Successfully read {len(dfs)} parquet files with {len(data_df)} total rows")
        return data_df
    else:
        print("No data found in parquet files")
        return pd.DataFrame()  # return empty df
# ------------


def download_file(url: str, local_file: str, chunk_size: int = 1024 * 1024) -> None:
    """
    Downloads a remote URL to a local file.

    Args:
        url (str): The remote URL.
        local_filename (str): The name of the local file to save the downloaded content.
        chunk_size (int): The size in bytes of each chunk. Defaults to 1024.

    Returns:
        None

    Example usage:
        download_file('http://example.com/file.txt', 'file.txt', chunk_size=1024*1024)  # Download in chunks of 1MB
    """
    # Check if the local file already exists
    if os.path.exists(local_file):
        file_size = format_size(os.path.getsize(local_file))
        print(f"Local file '{local_file}' ({file_size}) already exists. Skipping download.")
        return

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(local_file), exist_ok=True)

    # Stream the file download
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        print()
        file_size = format_size(os.path.getsize(local_file))
        print(f"{local_file} ({file_size}) downloaded successfully.")
## --- end: download_file ------

