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

import os

from data_processing.runtime import AbstractTransformLauncher
from data_processing.runtime.pure_python import PythonTransformLauncher
from data_processing.test_support.launch.transform_test import (
    AbstractTransformLauncherTest,
)
from dpk_filter.transform import (
    filter_columns_to_drop_cli_param,
    filter_criteria_cli_param,
    filter_logical_operator_cli_param,
    filter_logical_operator_default,
    filter_doc_id_column_name_cli_param,
    filter_input_arrow_folder_cli_param,
    filter_output_arrow_folder_cli_param
)
from dpk_filter.runtime import FilterPythonTransformConfiguration


class AbstractPythonFilterTransformTest(AbstractTransformLauncherTest):
    """
    Extends the super-class to define the test data for the tests defined there.
    The name of this class MUST begin with the word Test so that pytest recognizes it as a test class.
    """

    def _get_launcher(self) -> (AbstractTransformLauncher, dict):
        """
        Allow other runtimes to override with a different Launcher but share the test fixtures.
        Returns: the launcher and any additional command line/configuration included in the
        list of args given as the 2nd element of the fixtures.
        """
        return (PythonTransformLauncher(FilterPythonTransformConfiguration()), {})

    def _get_test_file_directory(self) -> str:
        raise NotImplemented

    def get_test_transform_fixtures(self) -> list[tuple]:
        fixtures = []
        basedir = self._get_test_file_directory()
        basedir = os.path.abspath(os.path.join(basedir, "../test-data"))

        launcher, args = self._get_launcher()
        fixtures.append(
            (
                launcher,
                args
                | {
                    filter_criteria_cli_param: [
                        "docq_total_words > 100 AND docq_total_words < 200",
                        "ibmkenlm_docq_perplex_score < 230",
                    ],
                    filter_logical_operator_cli_param: filter_logical_operator_default,
                    filter_columns_to_drop_cli_param: ["extra", "cluster"],
                },
                os.path.join(basedir, "input"),
                os.path.join(basedir, "expected", "test-and"),
            )
        )

        launcher, args = self._get_launcher()
        fixtures.append(
            (
                launcher,
                args
                | {
                    filter_criteria_cli_param: [
                        "docq_total_words > 100 AND docq_total_words < 200",
                        "ibmkenlm_docq_perplex_score < 230",
                    ],
                    filter_logical_operator_cli_param: "OR",
                    filter_columns_to_drop_cli_param: ["extra", "cluster"],
                },
                os.path.join(basedir, "input"),
                os.path.join(basedir, "expected", "test-or"),
            )
        )

        basedir = self._get_test_file_directory()
        output_arrow_dir = os.path.join(basedir, "../output")
        basedir = os.path.abspath(os.path.join(basedir, "../test-data/ds01"))

        launcher, args = self._get_launcher()
        fixtures.append(
            (
                launcher,
                args
                | {
                    filter_criteria_cli_param: [
                        "docq_total_words > 100 AND docq_total_words < 400",
                        "ibmkenlm_docq_perplex_score < 250",
                    ],
                    filter_logical_operator_cli_param: filter_logical_operator_default,
                    filter_columns_to_drop_cli_param: ["extra", "cluster"],
                    filter_doc_id_column_name_cli_param: "document_id",
			        filter_input_arrow_folder_cli_param: os.path.join(basedir, "input", "arrow"),
			        filter_output_arrow_folder_cli_param: os.path.join(output_arrow_dir, "arrow")
                },
                os.path.join(basedir, "input", "parquet"),
                os.path.join(basedir, "expected", "parquet"),
            )
        )

        # These test are also done in the python-only tests, so no real need to duplicate here.  They slow down ci/cd builds.
        # fixtures.append(
        #     (
        #         RayTransformLauncher(FilterRayTransformConfiguration()),
        #         {
        #             "run_locally": True,
        #             filter_criteria_cli_param: [],
        #             filter_logical_operator_cli_param: filter_logical_operator_default,
        #             filter_columns_to_drop_cli_param: [],
        #         },
        #         os.path.join(basedir, "input"),
        #         os.path.join(basedir, "expected", "test-default"),
        #     )
        # )
        #
        # fixtures.append(
        #     (
        #         RayTransformLauncher(FilterRayTransformConfiguration()),
        #         {
        #             "run_locally": True,
        #             filter_criteria_cli_param: [
        #                 "date_acquired BETWEEN '2023-07-04' AND '2023-07-08'",
        #                 "title LIKE 'https://%'",
        #             ],
        #             filter_logical_operator_cli_param: filter_logical_operator_default,
        #             filter_columns_to_drop_cli_param: [],
        #         },
        #         os.path.join(basedir, "input"),
        #         os.path.join(basedir, "expected", "test-datetime-like"),
        #     )
        # )
        #
        # fixtures.append(
        #     (
        #         RayTransformLauncher(FilterRayTransformConfiguration()),
        #         {
        #             "run_locally": True,
        #             filter_criteria_cli_param: [
        #                 "document IN ('CC-MAIN-20190221132217-20190221154217-00305.warc.gz', 'CC-MAIN-20200528232803-20200529022803-00154.warc.gz', 'CC-MAIN-20190617103006-20190617125006-00025.warc.gz')",
        #             ],
        #             filter_logical_operator_cli_param: filter_logical_operator_default,
        #             filter_columns_to_drop_cli_param: [],
        #         },
        #         os.path.join(basedir, "input"),
        #         os.path.join(basedir, "expected", "test-in"),
        #     )
        # )

        return fixtures
