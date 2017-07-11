
GIT_PORCELAIN_STATUS=$(shell git status --porcelain)

check-all-commited:
	if [ -n "$(GIT_PORCELAIN_STATUS)" ]; \
	then \
	    echo 'YOU HAVE UNCOMMITED CHANGES'; \
	    git status; \
	    exit 1; \
	fi
	
pypi-upload: check-all-commited 
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*

clean:
	-find . -name '*.py[co]' -exec rm {} \;

install:
	pip install -r requirements.txt