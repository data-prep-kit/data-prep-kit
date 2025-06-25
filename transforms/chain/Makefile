REPOROOT=../..
include $(REPOROOT)/.make.defaults


clean:
	rm -fr venv

venv::
	@# Help: Create the virtual environment using pyproject.toml
	$(PYTHON) -m venv venv
	source venv/bin/activate; \
	pip install $(REPOROOT)/data-processing-lib; \
	pip install "$(REPOROOT)/transforms[lang_id, doc_quality]"; \
	pip install pytest

test-src: venv
	source venv/bin/activate; \
	pip list; \
	pytest test

