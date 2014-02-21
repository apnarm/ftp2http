# TODO: is "make" a good tool for this? if so, do it properly.

INSTALLPATH = /usr/lib/ftp2http
PIP = $(INSTALLPATH)/bin/pip
PYTHON = $(INSTALLPATH)/bin/python
VIRTUALENV = virtualenv

.PHONY: all build install clean

all: build

build:
	make clean
	python setup.py sdist

clean:
	test -d build && rm -r build || true
	test -d dist && rm -r dist || true
	test -d ftp2http.egg-info && rm -r ftp2http.egg-info || true

install:
	
	# Create the virtual environment.
	test -e $(INSTALLPATH) && echo "Already installed to $(INSTALLPATH)" || true
	test -e $(INSTALLPATH) && exit 1 || true
	test -d $(INSTALLPATH) || $(VIRTUALENV) --no-site-packages --distribute $(INSTALLPATH)
	. $(INSTALLPATH)/bin/activate
	
	# Install ftp2http (and its dependencies).
	$(PIP) install dist/ftp2http-0.1.tar.gz
	
	# Make the ftp2http bin script available.
	alternatives --install /usr/bin/ftp2http ftp2http /usr/lib/ftp2http/bin/ftp2http 1
	
	# Copy the default config.
	test -e /etc/ftp2http.conf || cp conf/ftp2http.conf /etc/ftp2http.conf

uninstall:
	
	# Delete the program files.
	test -d $(INSTALLPATH) && rm -r $(INSTALLPATH) || true
	
	# Remove the bin script.
	alternatives --remove ftp2http /usr/lib/ftp2http/bin/ftp2http || true
	
	# Not deleting /etc/ftp2http.conf
	
	# DONE
