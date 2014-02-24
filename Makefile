.PHONY: all build clean

all: build

build:
	
	make clean
	
	# Build the python library.
	python setup.py sdist
	
	# Create the source file for the RPM.
	mkdir -p source/ftp2http-0.1
	cp conf/ftp2http.conf source/ftp2http-0.1
	cp dist/ftp2http-0.1.tar.gz source/ftp2http-0.1
	mkdir -p rpm/SOURCES
	cd source && tar -czf ../rpm/SOURCES/ftp2http-0.1.tar.gz *
	
	# Build the RPM.
	rpm/build.sh

clean:
	rm -rf build dist ftp2http.egg
	rm -rf source
	rm -rf rpm/BUILD/* rpm/BUILDROOT/*
