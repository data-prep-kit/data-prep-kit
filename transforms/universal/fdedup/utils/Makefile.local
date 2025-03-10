PYTHON=python
PIP=pip

venv:	requirements.txt
	$(PYTHON) -m venv venv
	if [ -e venv/Scripts/activate ]; then			\
		echo "For Windows please try the following AS Administrator - no guarantees";	\
		echo "  venv\\Scripts\\activate";		\
		echo "  pip install --upgrade pip";		\
		echo "  pip install -r requirements.txt";	\
		echo "  pip install pytest";		\
	else						\
		. venv/bin/activate;			\
		$(PIP) install --upgrade pip;		\
		$(PIP) install -r requirements.txt;	\
	fi					
set-versions:
	@: