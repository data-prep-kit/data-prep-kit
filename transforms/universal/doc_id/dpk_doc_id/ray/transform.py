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

## Depricated code
## Maintained for backwards compatibility with existing workflows
import warnings

from data_processing.utils import get_dpk_logger
logger = get_dpk_logger()


warnings.warn(
    f"This module is deprecated and will be removed in a future version. Use python -m dpk_doc_id.ray.runtime to avoid disruption in the future.", 
     DeprecationWarning, stacklevel=2
    )
logger.warning(
    f"This module is deprecated and will be removed in a future version. Use python -m dpk_doc_id.ray.runtime to avoid disruption in the future."
    )
from dpk_doc_id.ray.runtime import DocIDRayTransformRuntimeConfiguration
from data_processing_ray.runtime.ray import RayTransformLauncher


if __name__ == "__main__":
    launcher = RayTransformLauncher(DocIDRayTransformRuntimeConfiguration())
    launcher.launch()
