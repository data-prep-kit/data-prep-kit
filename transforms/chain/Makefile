REPOROOT=../..
include $(REPOROOT)/.make.defaults


clean:
	rm -fr venv

venv::
	@# Help: Create the virtual environment using pyproject.toml
	$(PYTHON) -m venv venv
	source venv/bin/activate; \
	$(PYTHON) -m pip install -e $(REPOROOT)/data-processing-lib; \
	$(PYTHON) -m pip install -e "$(REPOROOT)/transforms[lang_id, doc_quality, docling2parquet, doc_chunk]"; \
	$(PYTHON) -m pip install -r $(REPOROOT)/transforms/language/lang_id/requirements.txt; \
	$(PYTHON) -m pip install -r $(REPOROOT)/transforms/language/doc_quality/requirements.txt; \
	$(PYTHON) -m pip install -r $(REPOROOT)/transforms/language/docling2parquet/requirements.txt; \
	$(PYTHON) -m pip install -r $(REPOROOT)/transforms/language/doc_chunk/requirements.txt; \
	$(PYTHON) -m pip install pytest;
	## When running on Ubuntu as part of the github workflow, it is failing to install the extras \
	## Hence adding the specific requirements here for lang_id, doc_quality, docling2parquet, and doc_chunk



test-src: venv
	source venv/bin/activate; \
	pytest test

set-versions:
	echo "Do nothing"
