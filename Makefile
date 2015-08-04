$(eval VERSION := $(shell python setup.py --version))
SDIST := dist/ftp2http-$(VERSION).tar.gz

all: build

build: $(SDIST)

$(SDIST):
	python setup.py sdist
	python setup.py bdist_wheel
	rm -rf ftp2http.egg-info

.PHONY: upload
upload:
	python setup.py sdist upload
	python setup.py bdist_wheel upload
	rm -rf ftp2http.egg-info

.PHONY: clean
clean:
	rm -rf dist ftp2http.egg ftp2http.egg-info
