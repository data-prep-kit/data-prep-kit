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

from typing import Any, NamedTuple


def compute_common_params(
    worker_options: dict,  # ray worker configuration
    actor_options: dict,  # actor desired configuration
    data_s3_config: str,  # S3 configuration
    num_permutations: int,  # number of permutations (minhashes) per document
    n_samples: int,  # files to sample for number of documents estimation
) -> NamedTuple(
    "fdedup_params", [("num_segments", int), ("num_actors", str), ("actor_cpu", float), ("actor_memory", int)]
):
    """
    Compute fuzzy dedup execution parameters common to all the transforms
    :param worker_options: worker group configuration
    :param actor_options: desired actor configuration
    :param data_s3_config: s3 configuration
    :param num_permutations: number of permutations
    :param n_samples: number of samples used to estimate the total number of documents in the dataset
    :return: fdedup_params NamedTuple: num_segments - int, num_actors - str, cpus (float) and memory (int) per actor
    """

    import sys

    from data_processing.data_access import DataAccessS3
    from data_processing.utils import GB
    from runtime_utils import KFPUtils

    # get credentials
    s3_key, s3_secret, s3_endpoint = KFPUtils.credentials()
    s3_creds = {"access_key": s3_key, "secret_key": s3_secret, "url": s3_endpoint}
    s3_config = KFPUtils.load_from_json(data_s3_config.replace("'", '"'))
    # because S3 is the only viable version for kfp-based implementation, we are here creating DataAccess S3 directly
    data_access = DataAccessS3(s3_credentials=s3_creds, s3_config=s3_config, d_sets=None, checkpoint=False, m_files=-1)
    # sample input data
    sampling: dict[str, Any]
    sampling, _ = data_access.sample_input_data(n_samples=n_samples)
    number_of_docs = int(sampling.get("estimated number of docs"))
    if number_of_docs == 0:
        print(f"Estimated number of documents and documents size is zero. Please verify the input path.")
        sys.exit(1)
    print(f"Estimated number of docs: {number_of_docs}")
    actor_cpu: float = actor_options.get("num_cpus", 1)  # if num_cpus not specified, request 1 CPU per actor
    actor_memory: int = int(actor_options.get("memory", 16)) * GB  # if memory not specified, request 16 GB per actor
    # Calculate the number of segments
    # Assume each document takes doc_bytes = (8 + num_permutations * 4 + 20) bytes, where:
    #   8 bytes are taken by the band hash
    #   (num_permutations * 4) bytes are taken by the min hashes
    #   20 bytes to provide some extra space for storage in a table
    # The total amount of space needed by a band is number_of_docs * doc_bytes.
    # To scale band handling, divide each band into segments, each smaller than 1/6 of an actor's allocated memory
    doc_bytes = 8 + num_permutations * 4 + 20
    band_bytes = number_of_docs * doc_bytes
    num_segments = 1 + (band_bytes // (actor_memory // 6))
    print(f"Number of segments: {num_segments}")

    # Calculate number of actors, using KFPUtils.default_compute_execution_params()
    # Create new dict with memory expressed in bytes, as expected by KFPUtils.default_compute_execution_params()
    actor_config = {
        "num_cpus": actor_cpu,
        "memory": actor_memory,
    }
    num_actors = KFPUtils.default_compute_execution_params(str(worker_options), str(actor_config))

    print(f"num_actors = {num_actors}")
    from collections import namedtuple

    fdedup_params = namedtuple(
        typename="fdedup_params",
        field_names=["num_segments", "num_actors", "actor_cpu", "actor_memory"],
    )
    print(
        f"num_segments = {num_segments}, num_actors = {num_actors}, actor_cpu = {actor_cpu}, actor_memory = {actor_memory}"
    )
    return fdedup_params(num_segments, num_actors, actor_cpu, actor_memory)


def signature_calc_compute_execution_params(
    runtime_num_actors: str,  # number of actors computed by KFPUtils.default_compute_execution_params()
    runtime_actor_cpus: float,  # number of CPUS needed for each actor
    runtime_actor_memory: int,  # memory (in bytes) needed by each actor
    data_s3_config: str,  # s3 configuration
    data_max_files: int,  # max files to process
    data_num_samples: int,  # num samples to process
    runtime_pipeline_id: str,  # pipeline id
    runtime_job_id: str,  # job id
    runtime_code_location: dict,  # code location
    doc_column: str,  # document column name
    id_column: str,  # integer document id column name
    num_permutations: int,  # number of permutations
    num_bands: int,  # number of bands
    num_minhashes_per_band: int,  # band length
    word_shingle_size: int,  # number of words in shingle
    shingle_option: str,  # type of shingle, one of 'word' or 'char'
    threshold: float,  # threshold,
    num_segments: int,  # number of segments
    seed: int,  # seed for the random number generator
) -> dict:

    """
    Compute fuzzy dedup execution parameters for signature calculation
    :param runtime_num_actors: number of actors computed by KFPUtils.default_compute_execution_params()
    :param runtime_actor_cpus: number of CPUS needed for each actor
    :param runtime_actor_memory: memory (in bytes) needed by each actor
    :param data_s3_config: s3 configuration
    :param data_max_files: max files to process
    :param data_num_samples: num samples to process
    :param runtime_pipeline_id: pipeline id
    :param runtime_job_id: job id
    :param runtime_code_location: code location
    :param doc_column: document column name
    :param id_column: integer document id column name
    :param num_permutations: number of permutations
    :param num_bands: number of bands
    :param num_minhashes_per_band: band length
    :param word_shingle_size: number of words/chars in shingle
    :param shingle_option: str: type of shingle, one of 'word' or 'char'
    :param threshold: threshold,
    :param num_segments: number of segments
    :param seed: seed for the random number generator
    :return: dictionary with Ray Job execution parameters
    """

    # fuzzy parameters for signature calculation
    actor_options = {"num_cpus": runtime_actor_cpus, "memory": runtime_actor_memory}
    return {
        "data_s3_config": data_s3_config,
        "data_max_files": data_max_files,
        "data_num_samples": data_num_samples,
        "runtime_num_workers": runtime_num_actors,
        "runtime_worker_options": str(actor_options),
        "runtime_pipeline_id": runtime_pipeline_id,
        "runtime_job_id": runtime_job_id,
        "runtime_code_location": str(runtime_code_location),
        "minhash_contents_column": doc_column,
        "minhash_document_id_column": id_column,
        "minhash_num_permutations": num_permutations,
        "minhash_num_bands": num_bands,
        "minhash_num_minhashes_per_band": num_minhashes_per_band,
        "minhash_word_shingle_size": word_shingle_size,
        "minhash_shingle_option": shingle_option,
        "minhash_jaccard_similarity_threshold": threshold,
        "minhash_num_segments": num_segments,
        "minhash_seed": seed,
        "scdata_s3_config": data_s3_config,
    }


def cluster_analysis_compute_execution_params(
    runtime_num_actors: str,  # number of actors computed by KFPUtils.default_compute_execution_params()
    runtime_actor_cpus: float,  # number of CPUS needed for each actor
    runtime_actor_memory: int,  # memory (in bytes) needed by each actor
    data_s3_config: str,  # s3 configuration
    data_max_files: int,  # max files to process
    data_num_samples: int,  # num samples to process
    runtime_pipeline_id: str,  # pipeline id
    runtime_job_id: str,  # job id
    runtime_code_location: dict,  # code location
    num_bands: int,  # number of bands
    threshold: float,  # threshold,
    num_segments: int,  # number of segments
) -> dict:

    """
    Compute fuzzy dedup execution parameters for cluster analysis
    :param runtime_num_actors: number of actors computed by KFPUtils.default_compute_execution_params()
    :param runtime_actor_cpus: number of CPUS needed for each actor
    :param runtime_actor_memory: memory (in bytes) needed by each actor
    :param data_s3_config: s3 configuration
    :param data_max_files: max files to process
    :param data_num_samples: num samples to process
    :param runtime_pipeline_id: pipeline id
    :param runtime_job_id: job id
    :param runtime_code_location: code location
    :param num_bands: number of bands
    :param threshold: threshold,
    :param num_segments: number of segments
    :return: a dictionary with a Ray Job execution parameters
    """
    import json
    import os

    # fuzzy parameters
    # Get cluster parameters
    data_s3_config_dict = json.loads(data_s3_config.replace("'", '"'))
    base_folder = data_s3_config_dict.get("output_folder")
    data_s3_config_dict["input_folder"] = os.path.join(base_folder, "bands")
    data_s3_config_dict["output_folder"] = os.path.join(base_folder, "docs_to_remove")
    data_s3_config = json.dumps(data_s3_config_dict).replace('"', "'")
    actor_options = {"num_cpus": runtime_actor_cpus, "memory": runtime_actor_memory}
    return {
        "data_s3_config": data_s3_config,
        "data_max_files": data_max_files,
        "data_num_samples": data_num_samples,
        "runtime_num_workers": runtime_num_actors,
        "runtime_worker_options": str(actor_options),
        "runtime_pipeline_id": runtime_pipeline_id,
        "runtime_job_id": runtime_job_id,
        "runtime_code_location": str(runtime_code_location),
        "cluster_num_bands": num_bands,
        "cluster_jaccard_similarity_threshold": threshold,
        "cluster_num_segments": num_segments,
    }


def get_duplicate_list_compute_execution_params(
    runtime_num_actors: str,  # number of actors computed by KFPUtils.default_compute_execution_params()
    runtime_actor_cpus: float,  # number of CPUS needed for each actor
    runtime_actor_memory: int,  # memory (in bytes) needed by each actor
    data_s3_config: str,  # s3 configuration
    data_max_files: int,  # max files to process
    data_num_samples: int,  # num samples to process
    runtime_pipeline_id: str,  # pipeline id
    runtime_job_id: str,  # job id
    runtime_code_location: dict,  # code location
) -> dict:
    """
    Compute fuzzy dedup execution parameters for get duplicate list step
    :param runtime_num_actors: number of actors computed by KFPUtils.default_compute_execution_params()
    :param runtime_actor_cpus: number of CPUS needed for each actor
    :param runtime_actor_memory: memory (in bytes) needed by each actor
    :param data_s3_config: s3 configuration
    :param data_max_files: max files to process
    :param data_num_samples: num samples to process
    :param runtime_pipeline_id: pipeline id
    :param runtime_job_id: job id
    :param runtime_code_location: code location
    :return: a dictionary with a Ray Job execution parameters
    """
    import json
    import os

    # fuzzy parameters
    duplicate_docids_folder: str = "docs_to_remove"
    duplicate_list_location: str = os.path.join("docs_to_remove_consolidated", "docs_to_remove_consolidated.parquet")
    # Get cluster parameters
    data_s3_config_dict = json.loads(data_s3_config.replace("'", '"'))
    base_folder = data_s3_config_dict.get("output_folder")
    data_s3_config_dict["input_folder"] = base_folder
    data_s3_config_dict["output_folder"] = base_folder
    data_s3_config = json.dumps(data_s3_config_dict).replace('"', "'")
    actor_options = {"num_cpus": runtime_actor_cpus, "memory": runtime_actor_memory}
    return {
        "data_s3_config": data_s3_config,
        "data_max_files": data_max_files,
        "data_num_samples": data_num_samples,
        "runtime_num_workers": runtime_num_actors,
        "runtime_worker_options": str(actor_options),
        "runtime_pipeline_id": runtime_pipeline_id,
        "runtime_job_id": runtime_job_id,
        "runtime_code_location": str(runtime_code_location),
        "fdlist_docs_to_remove": duplicate_docids_folder,
        "fdlist_consolidated_filename": duplicate_list_location,
    }


def data_cleaning_compute_execution_params(
    runtime_num_actors: str,  # number of actors computed by KFPUtils.default_compute_execution_params()
    runtime_actor_cpus: float,  # number of CPUS needed for each actor
    runtime_actor_memory: int,  # memory (in bytes) needed by each actor
    data_s3_config: str,  # s3 configuration
    data_max_files: int,  # max files to process
    data_num_samples: int,  # num samples to process
    runtime_pipeline_id: str,  # pipeline id
    runtime_job_id: str,  # job id
    runtime_code_location: dict,  # code location
    id_column: str,  # integer document id column name
    operation_mode: str,  # filter (non-)duplicates or annotate
) -> dict:
    """
    Compute fuzzy dedup execution parameters
    :param runtime_num_actors: number of actors computed by KFPUtils.default_compute_execution_params()
    :param runtime_actor_cpus: number of CPUS needed for each actor
    :param runtime_actor_memory: memory (in bytes) needed by each actor
    :param data_s3_config: s3 configuration
    :param data_max_files: max files to process
    :param data_num_samples: num samples to process
    :param runtime_pipeline_id: pipeline id
    :param runtime_job_id: job id
    :param runtime_code_location: code location
    :param id_column: integer document id column name
    :param operation_mode: filter (non-)duplicates or annotate
    :return: a dictionary with a Ray Job execution parameters
    """
    import json
    import os

    # fuzzy parameters
    # Get cluster parameters
    data_s3_config_dict = json.loads(data_s3_config.replace("'", '"'))
    base_folder = data_s3_config_dict.get("output_folder")
    if operation_mode == "filter_duplicates":
        output_subfolder = "cleaned"
    elif operation_mode == "filter_non_duplicates":
        output_subfolder = "duplicates"
    else:  # operation_mode == "annotate"
        output_subfolder = "annotated"
    data_s3_config_dict["output_folder"] = os.path.join(base_folder, output_subfolder)
    data_s3_config = json.dumps(data_s3_config_dict).replace('"', "'")
    duplicate_list_location: str = os.path.join("docs_to_remove_consolidated", "docs_to_remove_consolidated.parquet")
    actor_options = {"num_cpus": runtime_actor_cpus, "memory": runtime_actor_memory}
    return {
        "data_s3_config": data_s3_config,
        "data_max_files": data_max_files,
        "data_num_samples": data_num_samples,
        "runtime_num_workers": runtime_num_actors,
        "runtime_worker_options": str(actor_options),
        "runtime_pipeline_id": runtime_pipeline_id,
        "runtime_job_id": runtime_job_id,
        "runtime_code_location": str(runtime_code_location),
        "fdclean_document_id_column": id_column,
        "fdclean_duplicate_list_location": duplicate_list_location,
        "fdclean_operation_mode": operation_mode,
    }
