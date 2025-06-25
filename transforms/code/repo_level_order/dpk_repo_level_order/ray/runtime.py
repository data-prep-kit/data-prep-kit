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

from dpk_repo_level_order.transform import *
from data_processing_ray.runtime.ray import (
    RayTransformLauncher,
    Transform
)
from data_processing.utils import ParamsUtils
import sys

class RepoLevelOrderRuntime(DefaultRayTransformRuntime):
    """
    RepoLevelOrder runtime support.
    This runtime creates and initialises a store which can store
    information as a key/value dict like structure
    { groups: list of files where group is found}. The transform
    populates the store and the `compute_execution_stats` method of this
    runtime reads the store to do actually read the files
    per group and apply the selected transformations (sorting/combining rows)
    and writes a parquet file per group.
    """

    def __init__(self, params: dict[str, Any]):
        """
        Create filter runtime
        :param params: parameters, that should include
            sorting_enabled - True if sorting is enabled, it is an optional parameter.
            sorting_algo_key - One of [SORT_BY_PATH, SORT_SEMANTIC, SORT_SEMANTIC_NORMALISED, None]
            ray_workers - Number of ray workers to grouped and process data
            ray_num_cpus - Number of cpus per Ray Actor.
            output_by_langs_key - Bool, if True, the output files are written to language folder
            output_superrows_key - Bool, if True, all rows in output are collated toa single row.
            store_params - A dictionary to create/update store, used by transform and runtime.

        """
        self.logger = get_logger(__name__)
        super().__init__(params)

        self.stage_one_only = self.params[stage_one_only_key]
        self.sorting_enabled = self.params[sorting_enable_key]
        self.sorting_algo = self.params[sorting_algo_key]

        self.output_by_langs = self.params[output_by_langs_key]
        self.combine_rows = self.params[output_superrows_key]
        self.ray_workers = self.params[stage_two_ray_workers_key]
        self.ray_num_cpus = self.params[stage_two_ray_cpus_key]

    def _initialize_store_params(self):

        store_params = self.params[store_params_key]

        self.params[store_params_key] = self.params[store_params_key] | init_store_params(store_params, self.logger)
        self.store_backend_dir = None

        return True

    def get_transform_config(
        self,
        data_access_factory: DataAccessFactoryBase,
        statistics: ActorHandle,
        files: list[str],
    ) -> dict[str, Any]:
        """
        Set environment for transform execution
        :param data_access_factory - data access factory
        :param statistics - reference to the statistics object
        :param files - list of files to process
        :return: dictionary of transform init params
        """
        self.logger.info("=> get_transform_config started")
        self.store_backend_dir = self.params[store_dir_key]
        data_access = data_access_factory.create_data_access()
        self.input_folder = data_access.input_folder
        self.output_folder = data_access.output_folder
        self.daf = data_access_factory
        self.data_access = data_access
        self._initialize_store_params()
        self.store_params = self.params[store_params_key]
        self.logger.info("<= get_transform_config")
        self.start_time = datetime.datetime.now()
        self.repo_column_name = self.params[grouping_column_key]
        self.language_column_name = self.params[language_column_key]
        return self.params

    def _prepare_mapper_function(self):
        # Prepare mapper function according to cli args
        # this function wraps the mappings to be done on a table
        # here whether we want sorting or superrows or even
        # want output folders arranged by language
        mapper_function_params = {}

        from dpk_repo_level_order.internal.repo_level_wrappers import (
            get_dominant_language_func,
            get_transforming_func,
        )

        if self.sorting_enabled:
            self.logger.info(f"Repo level sorting is enabled. Algo: {self.sorting_algo}")
            from dpk_repo_level_order.internal.repo_level_wrappers import (
                SORT_BY_PATH,
                SORT_SEMANTIC,
                SORT_SEMANTIC_NORMALISED,
                get_sorting_func,
            )

            sort_func = get_sorting_func(self.sorting_algo, "title", self.logger, self.language_column_name)
            # Add sort_func to params
            mapper_function_params = mapper_function_params | {
                "sorting_func": sort_func,
            }

        if self.output_by_langs:
            self.logger.info("Output by language enabled.")
            mapper_function_params = mapper_function_params | {
                "filename_func": get_dominant_language_func(
                    language_column_name=self.language_column_name, title_column_name="title"
                ),
            }

        if self.combine_rows:
            self.logger.info("Combine rows enabled.")
            from dpk_repo_level_order.internal.repo_level_wrappers import superrow_table

            mapper_function_params = mapper_function_params | {"superrows_func": superrow_table}

        mapper_function_params = mapper_function_params | {"language_column_name": self.language_column_name}
        repo_mapper_func = get_transforming_func(**mapper_function_params)
        return repo_mapper_func

    def _prepare_inputs(self):
        store = create_store(self.store_params)
        store_type = self.store_params[store_type_key]

        p_input = []
        for repo, files in store.items_kv():
            if store_type == store_type_value_ray:
                p_input.append((repo, [f"{file}" for file in files]))
            else:
                files_location = self.input_folder
                p_input.append((repo, [f"{files_location}/{file}" for file in files]))
        return p_input

    def _group_and_sort(self):

        self.logger.info(f"Stage 1 Finished in {datetime.datetime.now() - self.start_time}.")

        from dpk_repo_level_order.internal.repo_grouper import GroupByRepoActor
        from ray.util import ActorPool

        p_input = self._prepare_inputs()
        if self.stage_one_only:
            return {"nrepos": len(p_input)}

        repo_mapper_func = self._prepare_mapper_function()
        processors = RayUtils.create_actors(
            clazz=GroupByRepoActor,
            params={
                "repo_column_name": self.repo_column_name,
                "output_dir": self.output_folder,
                "data_access_factory": self.daf,
                "mapper": repo_mapper_func,
            },
            actor_options={"num_cpus": self.ray_num_cpus},
            n_actors=self.ray_workers,
        )

        p_pool = ActorPool(processors)
        self.logger.info(f"Processing {len(p_input)} repos with {self.ray_workers} workers")
        replies = list(p_pool.map_unordered(lambda a, x: a.process.remote(x[0], x[1]), p_input))
        return {"nrepos": len(p_input)}

    def compute_execution_stats(self, stats: dict[str, Any]) -> dict[str, Any]:
        """
        Compute execution statistics
        :param stats: output of statistics
        :return: job execution statistics
        """
        # Get filters stats
        self.logger.info(f"Store Backend is {self.store_backend_dir}")
        second_stage_stats = self._group_and_sort()
        self.logger.info(f"Finished the transform in {datetime.datetime.now() - self.start_time} ")
        return stats | second_stage_stats


class RepoLevelOrderRayTransformConfiguration(RayTransformRuntimeConfiguration):
    def __init__(self):
        super().__init__(
            transform_config=RepoLevelOrderTransformConfiguration(),
            runtime_class=RepoLevelOrderRuntime,
        )


class RepoLevelOrder(Transform):
    def __init__(self, **kwargs):
        super().__init__(RepoLevelOrderRayTransformConfiguration(), **kwargs)


if __name__ == "__main__":
    launcher = RayTransformLauncher(RepoLevelOrderRayTransformConfiguration())
    launcher.launch()