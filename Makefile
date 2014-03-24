.PHONY: all build clean

all: build

build:
	
	make clean
	
	# Get the current version number.
	$(eval VERSION := $(shell python setup.py --version))
	
	# Build the python library.
	python setup.py sdist
	
	# Create the source file for the RPM.
	mkdir -p source/ftp2http-$(VERSION)
	cp conf/ftp2http.conf source/ftp2http-$(VERSION)
	cp dist/ftp2http-$(VERSION).tar.gz source/ftp2http-$(VERSION)
	mkdir -p rpm/SOURCES
	cd source && tar -czf ../rpm/SOURCES/ftp2http-$(VERSION).tar.gz *
	
	# Build the RPM.
	rpm/build.sh $(VERSION)

clean:
	rm -rf build dist ftp2http.egg
	rm -rf source
	rm -rf rpm/BUILD/* rpm/BUILDROOT/*
