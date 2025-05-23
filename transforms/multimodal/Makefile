REPOROOT=../..
# Use make help, to see the available rules
include $(REPOROOT)/transforms/.make.cicd.targets

#
# This is intended to be included across the Makefiles provided within
# a given transform's directory tree,  so must use compatible syntax.
#
################################################################################
# This defines the name of the transform and is used to match against
# expected files and is used to define the transform's image name. 
TRANSFORM_NAME=mm

################################################################################
TRANSFORM_PYTHON_SRC="-m dpk_$(TRANSFORM_NAME).faces.runtime"
TRANSFORM_RAY_SRC="-m dpk_$(TRANSFORM_NAME).ray.faces.runtime"


# large files are stored in seperate git repo or can be obtained from HF
models: models/yolov8m_200e.pt models/yolov8m-seg.pt models/yolov8n-face.pt

models/yolov8n-face.pt:
	@echo Downloading $@
	mkdir -p models
#	curl -L --output models/yolov8n-face.pt https://github.com/touma-I/large-files/raw/refs/heads/main/models/yolov8n-face.pt
	curl -L --output models/yolov8n-face.pt https://github.com/lindevs/yolov8-face/releases/latest/download/yolov8n-face-lindevs.pt

models/yolov8m_200e.pt:
	@echo Downloading $@
	mkdir -p models
	curl -L --output models/yolov8m_200e.pt https://huggingface.co/ZiqianLiu/yolov8_face/resolve/4b1db35121179d189754a3bf0b4a86aa44c03eef/yolov8m_200e.pt


models/yolov8m-seg.pt:
	@echo Downloading $@
	mkdir -p models
#	curl -L --output models/yolov8m-seg.pt https://github.com/touma-I/large-files/raw/refs/heads/main/models/yolov8m-seg.pt
	curl -L --output models/yolov8m-seg.pt https://huggingface.co/thejagstudio/textilev1Plain/resolve/69cc72e30cb576392ce6113ef41aa3779d656dfc/yolov8m-seg.pt

venv:: models

generate-test-data: venv
	- rm -fr test-data/faces/expected
	- rm -fr test-data/people/expected
	- rm -fr test-data/nsfw/expected
	source venv/bin/activate && \
	$(PYTHON) -m dpk_mm.faces.runtime \
        --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/faces/expected'}"
	source venv/bin/activate && \
	$(PYTHON) -m dpk_mm.people.runtime \
        --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/people/expected'}"
	source venv/bin/activate && \
	$(PYTHON) -m dpk_mm.nsfw.runtime \
        --data_local_config "{ 'input_folder' : 'test-data/input', 'output_folder' : 'test-data/nsfw/expected'}"

faces_test: venv
	@# Help: Run pytest on the test directory inside the venv 
	source venv/bin/activate; \
	export PYTHONPATH=. ;  \
	$(PYTEST) test/$@
	
nsfw_test: venv
	@# Help: Run pytest on the test directory inside the venv 
	source venv/bin/activate; \
	export PYTHONPATH=. ;  \
	$(PYTEST) test/$@

people_test: venv
	@# Help: Run pytest on the test directory inside the venv 
	source venv/bin/activate; \
	export PYTHONPATH=. ;  \
	$(PYTEST) test/$@

test-local: venv
	@# Help: Run pytest on the test directory inside the venv 
	source venv/bin/activate ; $(PYTHON) -m dpk_mm.faces.local
	source venv/bin/activate; $(PYTHON) -m dpk_mm.nsfw.local
	source venv/bin/activate; $(PYTHON) -m dpk_mm.people.local
	










