ftp2http
========

An FTP server that pushes uploaded files directly to a HTTP URL.

Overview
========

Think of ftp2http as a simple FTP layer that sits before a HTTP server.

| An FTP client connects to an ftp2http server and uploads a file. The
  ftp2http
| server immediately uploads that file to the configured HTTP URL.

| The server directory always appears empty to the client, even after a
  file has
| been uploaded. This is because uploaded files are only sent to the
  HTTP server,
| not stored.

Installation
============

Install ftp2http by using pip, a tool for managing Python packages.

#. Run ``pip install ftp2http``
#. Create a configuration file at ``/etc/ftp2http.conf``

-  Example:
   https://github.com/apn-online/ftp2http/blob/master/conf/ftp2http.conf

Usage
=====

-  Run ``ftp2http``

| We use **circusd** to manage the ftp2http process. An example
  configuration has
| been provided in the **examples** directory.

Authentication
==============

| Authentication can be checked against user accounts specified in the
| configuration file, or by configuring an authentication backend URL.

User accounts in the the configuration file
-------------------------------------------

| A specific configuration format is used, which can be generated using
  the
| ``ftp2http -a`` command.

Example:

::

    $ ftp2http -a
    Enter a username: dogman
    Enter a password:
    Confirm password:

    Add the following line to your configuration file.
    user: dogman:$2a$12$5NyFA4AbEfmZiexG62qIieBu/isqwTYnta8H9gH5zC0lCRVKyMrc.

HTTP Basic Authentication
-------------------------

| FTP login authentication can be performed via HTTP requests, using
  HTTP basic
| authentication. Set one or more **authentication\_backend** entries in
  the
| configuration file, and then ftp2http will perform requests to check
  the FTP
| login details. Login details are accepted if an
  authentication\_backend URL
| returns a 2xx response.

| File uploads themselves can also use HTTP basic authentication. By
  enabling
| **http\_basic\_auth** in the configuration file, ftp2http will reuse
  the FTP
| login details for HTTP basic authentication when sending uploaded
  files
| to the target URL.
