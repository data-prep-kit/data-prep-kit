import os
import requests
from humanfriendly import format_size
import pandas as pd
import glob
import magic
from dpk_connector.core.utils import (
    urlparse_cached
)
from urllib.parse import unquote


## Reads parquet files in a folder into a pandas dataframe
def read_parquet_files_as_df (parquet_dir):
    parquet_files = glob.glob(f'{parquet_dir}/*.parquet')

    # read each parquet file into a DataFrame and store in a list
    dfs = [pd.read_parquet (f) for f in parquet_files]

    # Concatenate all DataFrames into a single DataFrame
    data_df = pd.concat(dfs, ignore_index=True)
    return data_df


def download_file(url, local_file, chunk_size=1024*1024):
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

def get_mime_type(byte_data: bytes) -> str:
    """
    Obtain the MIME type for provided byte data using the magic library.

    Args:
        byte_data: bytes: Bytes data to identify mimetype for.
        
    Returns:
        str: Mimetype for given bytes data.
        
    Example:
        >>> byte_data = b'<!DOCTYPE html>\n...'
        >>> get_mime_type(byte_data)
        'text/html'
    """
    
    # Validate input type
    if not isinstance(byte_data, bytes):
        raise TypeError("Input must be of type 'bytes'")

    # Initialize a magic object for MIME type detection
    mime = magic.Magic(mime=True)

    # Return MIME type from the byte data
    return mime.from_buffer(byte_data)


def get_extension(url: str) -> str:
    parsed = urlparse_cached(url)
    path = parsed.path
    filename = unquote(os.path.basename(path))
    ext = os.path.splitext(filename)[1]
    if 16 < len(ext):
        ext = ext[:16]
    return ext


def get_filename_from_url(url: str) -> str:
    parsed = urlparse_cached(url)
    basename = unquote(os.path.splitext(os.path.basename(parsed.path))[0])
    ext = get_extension(url)
    return basename + ext