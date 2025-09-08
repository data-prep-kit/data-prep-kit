from enum import Enum
from typing import TypedDict


class TransformConstants:
    # Defines constants that are used across multiple transforms
    NAME = "name"
    ID = "id"
    DESCRIPTION = "description"
    JOB_ID = "job_id"
    JOB_RUN_ID = "job_run_id"
    CONTEXT_ID = "context_id"
    OUTPUT_FEATURES_TO_DROP = 'output_features_to_drop'
    TYPE = "type"
    AVAILABLE_FOR_FILTER = "available_for_filter"
    AVAILABLE_FOR_VECTOR_DB = "available_for_vector_db"
    MANDATORY_FOR_VECTOR_DB = "mandatory_for_vector_db"
    SKIPPED_DOCS = "skipped_docs"



class TransformCategory(str, Enum):
    Extract = "Extract"
    Ingest = "Ingest"
    Functional = "Functional"
    Quality = "Quality"
    VectorDB = "VectorDB"
    Custom = "Custom"

class ExecutionStatus(str, Enum):
    QUEUED = "Queued"
    STARTING = "Starting"
    RUNNING = "Running"
    PAUSED = "Paused"
    RESUMING = "Resuming"
    CANCELING = "Canceling"
    CANCELED = "Canceled"
    FAILED = "Failed"
    COMPLETED = "Completed"
    COMPLETED_WITH_ERRORS = "CompletedWithErrors"
    COMPLETED_WITH_WARNINGS = "CompletedWithWarnings"

class ValidationStatus(str, Enum):
    FAILED = "FAILED"
    SUCCEEDED = "SUCCEEDED"
    SUCCEEDED_WITH_WARNINGS = "SUCCEEDED_WITH_WARNINGS"

class Metrics:
    class External:
        JOB_RUN_STATUS = 'job_run_status'
        TOTAL_DOCS = "total_docs_count"
        TOTAL_DOCS_COUNT_FROM_LOGS = "total_docs"
        PROCESSED_DOCS = "processed_docs"
        PROCESSED_ROWS = "processed_rows"
        FAILED_DOCS_COUNT = "failed_docs_count"
        FAILED_DOCS = "failed_docs"
        SKIPPED_DOCS_COUNT = "skipped_docs_count"
        SKIPPED_DOCS = "skipped_docs"
        TOT_PAGES_CONVERTED = "tot_pages_converted"
        NODE_STATUS = "node_status"

    class Internal:
        DELETED_DOCS_COUNT = "deleted_docs_count"
        ALL_DOC_IDS = "all_doc_ids"


class DocsStructure(TypedDict):
    id: str
    name: str
    reason: str