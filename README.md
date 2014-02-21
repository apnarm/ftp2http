ftp2http
========

This is a write-only FTP server. No files can be downloaded from this server.
All received files are sent to a HTTP URL endpoint for processing.

It uses temporary files because Django (our endpoint) does not support chunked
encoding for POST requests. It only supports multipart encoding, and requires a
content-length header. Because the FTP protocol does not send the size of a file
before it begins uploading, the entire file must be received before its size can
be determined. This means that the HTTP request only starts when the file is
100% uploaded.
