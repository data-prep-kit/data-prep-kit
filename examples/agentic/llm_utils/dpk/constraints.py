# constraints = "constraint: If a plan has 'exact_dedup' and 'fuzzy_dedup' steps then 'exact_dedup' must run before 'fuzzy_dedup'.\n"
constraints = ""
constraints = constraints + "constraint: If the 'exact_dedup' tool is needed then it must run as the first step or immediately after 'Pdf2Parquet'.\n"
constraints = constraints + "constraint: If the 'tokenization' transform is needed then it must run as the last transform of the plan. Otherwise, it should not be part of the plan.\n"
constraints = constraints + "constraint: run 'Pdf2Parquet' tool as a first step if the input is pdf files.\n"

# constraints = constraints + "constraint: 'document_id' tool must run before 'fuzzy_dedup'.\n"
# constraints = constraints + "constraint: If a plan has a 'fuzzy_dedup' tool then it must run as earlier as possible.\n"
# constraints = constraints + "constraint: If a plan has a 'exact_dedup' tool then it must run as the first step or after 'Pdf2Parquet'.\n"