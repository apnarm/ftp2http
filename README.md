ftp2http
========

An FTP server that pushes uploaded files directly to a HTTP URL.


What does it do?
================

Think of ftp2http as a simple FTP layer that sits before a HTTP server.

An FTP client connects to an ftp2http server and uploads a file. The ftp2http
server immediately uploads that file to a configured HTTP URL.

Files are not downloaded from an ftp2http server. The FTP server appears
empty to FTP clients.


Building and installing
=======================

Minimal effort has been put into the build scripts at this stage.
We are using Scientific Linux 6 to build an x86_64 RPM.

Build RPM:

    $ cd ftp2http
    $ make

Install RPM:

    $ cd ftp2http
    $ rpm -i rpm/RPMS/x86_64/ftp2http-0.1-1.x86_64.rpm`


Usage
=====

* Install ftp2http
* Configure server by editing /etc/ftp2http.conf
* Run: `ftp2http`


User Accounts
============

User accounts are read from the ftp2http configuration file. A specific
format is used, which can be generated using the `ftp2http -a` command.

Example:

    $ ftp2http -a
    Enter a username: dogman
    Enter a password:
    Confirm password:
    
    Add the following line to your configuration file.
    user: dogman:$2a$12$5NyFA4AbEfmZiexG62qIieBu/isqwTYnta8H9gH5zC0lCRVKyMrc.

HTTP Basic Authentication
-------------------------

Authentication can also be used on the HTTP URL. By enabling **http_basic_auth**
in the configuration file, ftp2http will reuse the FTP username and password
for HTTP basic authentication. Of course, the HTTP URL will need to be set up
with the same accounts as your ftp2http server.
