import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

eng_content = "weather_en.txt"
eng_url = "weather_url_en.txt"

gr_content = "weather_gr.txt"
gr_url = "weather_url_gr.txt"

fr_content = "weather_fr.txt"
fr_url = "weather_url_fr.txt"

jp_content = "weather_jp.txt"
jp_url = "weather_url_jp.txt"

content_file_names = [eng_content, gr_content, fr_content, jp_content, eng_content ]
url_file_names = [eng_url, gr_url, fr_url, jp_url, eng_url]

contents = []
urls = []
for file_name in content_file_names:
    file = open(file_name, "r")
    content = file.read()
    contents.append(content)
for file_name in url_file_names:
    file = open(file_name, "r")
    content = file.read()
    urls.append(content)

print(f"{len(contents)}  {len(urls)}")

data = {
    "contents": contents,
    "urls": urls
}

table = pa.table(data)
#print(table)

output_file = 'sample1.parquet'
pq.write_table(table, output_file)