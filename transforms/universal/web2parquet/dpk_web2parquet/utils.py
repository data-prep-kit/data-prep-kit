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


from urllib.parse import urlparse

def get_file_info(url: str, headers: dict=None):
    try:
        file_size = int(headers['Content-Length'])
    except:
        file_size=0        
    try:
        content_type=headers.get('Content-Type')
    except:
        content_type='text/html'
        
    url_parse=urlparse(url)
    try:
        filename = headers.get('Content-Disposition').split('filename=')[1].strip().strip('"')
    except:
        filename='-'.join(url_parse.path.strip('/').split('/'))
    # Prepend host name 
    filename=url_parse.netloc.replace('.',"_")+'_'+filename
    
    # append extension using content type
    filename = filename+"_"+content_type.split(';')[0].replace("/", ".")
    return {'filename':filename, 'content_type': content_type, 'file_size': file_size}


