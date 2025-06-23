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


from dpk_web2parquet.transform import Web2Parquet

# create parameters

if __name__ == "__main__":
    # Here we show how to run outside of the runtime
    # Create and configure the transform.
    transform = Web2Parquet(urls= ['https://thealliance.ai/'],
                                    depth=1, 
                                    downloads=1)
    table_list, metadata = transform.transform()
    #print(f"\noutput table: {table_list}")
    print(f"output metadata : {metadata}")