init:
	pip install -r requirements/common.txt

test:
	pip install -r requirements/dev.txt
	python setup.py test

dist:
	python setup.py bdist

install:
	python production.py install

docs:
	python setup.py docs

