
# Directories in the transforms/universal directory for which we want to generate test workflows
UNIVERSAL_TRANSFORMS=doc_id ededup fdedup filter html2parquet noop profiler resize tokenization
# Directories in the transforms/code directory for which we want to generate test workflows
CODE_TRANSFORMS=code2parquet code_quality header_cleanser malware proglang_select repo_level_ordering
# Directories in the transforms/language directory for which we want to generate test workflows
LANG_TRANSFORMS=doc_chunk doc_quality lang_id docling2parquet pii_redactor text_encoder


# A list that holds transforms that should not be tested with KFP

transform-tests:
	-rm -rf test-universal-*.yml
	$(MAKE) TRANSFORM_SUBDIR=universal .transform-tests
	-rm -rf test-language-*.yml
	$(MAKE) TRANSFORM_SUBDIR=language .transform-tests
	-rm -rf test-code-*.yml
	$(MAKE) TRANSFORM_SUBDIR=code .transform-tests
	-rm -rf test-images-*.yml
	$(MAKE) TRANSFORM_SUBDIR=images .transform-tests


# Expects
#   TRANSFORM_SUBDIR  transforms subdirectory (such as universal)
.transform-tests:
	@for i in $$(find ../../transforms/$(TRANSFORM_SUBDIR) -mindepth 1 -maxdepth 1 -type d); do	\
	    z=$$(ls $$i/Makefile*);							\
	    if [ ! -z "$$z" ]; then							\
	        dir=$$(basename $$i);							\
	        yml=test-$(TRANSFORM_SUBDIR)-$$dir.yml;					\
	        echo Generating $$yml;							\
	        cat test-transform.template | sed -e "s?@TARGET_TRANSFORM_DIR@?transforms/$${TRANSFORM_SUBDIR}/$$dir?g" > $$yml;	\
	    fi;										\
	done








