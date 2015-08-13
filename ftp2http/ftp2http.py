"""
This is a write-only FTP server. No files can be downloaded from this server.
All received files are sent to a HTTP URL endpoint for processing.

It uses temporary files because Django (our endpoint) does not support chunked
encoding for POST requests. It only supports multipart encoding, and requires a
content-length header. Because the FTP protocol does not send the size of a file
before it begins uploading, the entire file must be received before its size can
be determined. This means that the HTTP request only starts when the file is
100% uploaded.

"""

import base64
import bcrypt
import errno
import os
import socket
import sys
import tempfile

from pyftpdlib.authorizers import AuthenticationFailed, DummyAuthorizer
from pyftpdlib.filesystems import AbstractedFS, FilesystemError
from pyftpdlib.handlers import _AsyncChatNewStyle, DTPHandler, FTPHandler, TLS_DTPHandler, TLS_FTPHandler
from pyftpdlib.log import logger
from pyftpdlib.servers import MultiprocessFTPServer

from swiftclient.client import http_connection


class UnexpectedHTTPResponse(Exception):
    pass


class PostFS(AbstractedFS):

    def validpath(self, path):
        """
        Check whether the path belongs to the user's home directory.
        Expected argument is a "real" filesystem pathname.

        Pathnames escaping from user's root directory are considered
        not valid.

        Overridden to not access the filesystem at all.

        """
        assert isinstance(path, unicode), path
        root = os.path.normpath(self.root)
        path = os.path.normpath(path)
        if not root.endswith(os.sep):
            root = root + os.sep
        if not path.endswith(os.sep):
            path = path + os.sep
        if path[0:len(root)] == root:
            return True
        return False

    # --- Wrapper methods around open() and tempfile.mkstemp

    def open(self, filename, mode):

        assert isinstance(filename, unicode), filename

        if mode not in ('w', 'wb'):
            raise FilesystemError('open mode %s: filesystem operations are disabled.' % mode)

        directory, filename = os.path.split(filename)
        username = os.path.basename(directory)
        if self.cmd_channel.authorizer._password_cache:
            password = self.cmd_channel.authorizer._password_cache[username]
        else:
            password = None

        return self.post_file(filename, username, password)

    def mkstemp(self, suffix='', prefix='', dir=None, mode='wb'):
        raise FilesystemError('mkstemp: filesystem operations are disabled.')

    # --- Wrapper methods around os.* calls

    def chdir(self, path):
        pass

    def mkdir(self, path):
        raise FilesystemError('mkdir: filesystem operations are disabled.')

    def listdir(self, path):
        return []

    def rmdir(self, path):
        raise FilesystemError('rmdir: filesystem operations are disabled.')

    def remove(self, path):
        raise FilesystemError('remove: filesystem operations are disabled.')

    def rename(self, src, dst):
        raise FilesystemError('rename: filesystem operations are disabled.')

    def chmod(self, path, mode):
        raise FilesystemError('chmod: filesystem operations are disabled.')

    def stat(self, path):
        raise FilesystemError('stat: filesystem operations are disabled.')

    def lstat(self, path):
        raise FilesystemError('lstat: filesystem operations are disabled.')

    def readlink(self, path):
        raise FilesystemError('readlink: filesystem operations are disabled.')

    # --- Wrapper methods around os.path.* calls

    def isfile(self, path):
        assert isinstance(path, unicode), path
        return False

    def islink(self, path):
        assert isinstance(path, unicode), path
        return False

    def isdir(self, path):
        assert isinstance(path, unicode), path
        return path == self.root

    def getsize(self, path):
        raise FilesystemError('getsize: filesystem operations are disabled.')

    def getmtime(self, path):
        raise FilesystemError('getmtime: filesystem operations are disabled.')

    def realpath(self, path):
        assert isinstance(path, unicode), path
        return path

    def lexists(self, path):
        assert isinstance(path, unicode), path
        return False

    def get_user_by_uid(self, uid):
        return 'owner'

    def get_group_by_gid(self, gid):
        return 'group'

    # --- Listing utilities

    def get_list_dir(self, path):
        """"
        Return an iterator object that yields a directory listing
        in a form suitable for the LIST command.

        """
        assert isinstance(path, unicode), path
        return self.format_list(path, [])


class MultipartPostFile(object):

    url = None

    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'

    def __init__(self, filename, username, password):
        self.name = filename
        self.username = username
        self.password = password
        self.closed = False

    def write(self, data):

        if not hasattr(self, 'request_body'):

            self.request_body = tempfile.SpooledTemporaryFile()

            self.request_body.write('--' + self.BOUNDARY)
            self.request_body.write(self.CRLF)
            self.request_body.write('Content-Disposition: form-data; name="%s"; filename="%s"' % (self.username, self.name))
            self.request_body.write(self.CRLF)
            self.request_body.write('Content-Type: application/octet-stream')
            self.request_body.write(self.CRLF)
            self.request_body.write(self.CRLF)

        self.request_body.write(data)

    def close(self):

        if not self.closed and hasattr(self, 'request_body'):

            try:

                self.request_body.write(self.CRLF)
                self.request_body.write('--' + self.BOUNDARY + '--')
                self.request_body.write(self.CRLF)

                length = self.request_body.tell()

                try:

                    parsed_url, connection = http_connection(self.url)

                    if parsed_url.query:
                        url_path = parsed_url.path + '?' + parsed_url.query
                    else:
                        url_path = parsed_url.path

                    connection.putrequest('POST', url_path)

                    connection.putheader('Content-Type', 'multipart/form-data; boundary=%s' % self.BOUNDARY)
                    connection.putheader('Content-Length', str(length))

                    if self.password:
                        credentials = base64.b64encode(b'%s:%s' % (self.username, self.password))
                        connection.putheader('Authorization', 'Basic %s' % credentials)

                    connection.endheaders()

                    self.request_body.seek(0)
                    connection.send(self.request_body)

                    response = connection.getresponse()

                except Exception as error:
                    raise UnexpectedHTTPResponse('%s: %s' % (error.__class__, error))

                if response.status // 100 != 2:

                    message = '%d: %s' % (response.status, response.reason)

                    if response.getheader('Content-Type') == 'text/plain':
                        try:
                            response_content = response.read(100).splitlines()[0]
                            message = '%s. %s' % (message, response_content)
                        except Exception:
                            pass

                    raise UnexpectedHTTPResponse(message)

            finally:
                self.closed = True
                self.request_body.close()

#
# Using chunked transfer encoding would be preferable over multipart form
# data, but it is not supported by Django or WSGI or whatever. Keeping it
# here just in case.
#
#class ChunkedPostFile(object):
#
#    url = None
#
#    def __init__(self, name):
#        self.name = name
#        self.closed = False
#
#    def write(self, data):
#
#        if not hasattr(self, 'connection'):
#
#            parsed_url, self.connection = http_connection(self.url)
#
#            self.connection.putrequest('POST', parsed_url.path + '?path=' + self.name)
#
#            self.connection.putheader('Content-Type', 'application/octet-stream')
#            self.connection.putheader('Transfer-Encoding', 'chunked')
#
#            self.connection.endheaders()
#
#        length = len(data)
#        self.connection.send('%X\r\n' % length)
#        self.connection.send(data)
#        self.connection.send('\r\n')
#
#    def close(self):
#
#        if not self.closed and hasattr(self, 'connection'):
#
#            try:
#
#                self.connection.send('0\r\n\r\n')
#
#                response = self.connection.getresponse()
#
#                if response.status // 100 != 2:
#                    raise UnexpectedHTTPResponse('%d: %s' % (response.status, response.reason))
#
#            finally:
#                self.closed = True
#                self.connection.close()


class PostDTPHandlerMixin(object):

    def close(self):
        """
        Extend the class to close the file earlier than usual, making the HTTP
        upload occur before a response is sent to the FTP client. In the event
        of an unsuccessful HTTP upload, relay the HTTP error message to the
        FTP client by overriding the response.

        """

        if self.receive and self.transfer_finished and not self._closed:
            if self.file_obj is not None and not self.file_obj.closed:
                try:
                    self.file_obj.close()
                except UnexpectedHTTPResponse as error:
                    self._resp = ('550 Error transferring to HTTP - %s' % error, logger.error)

        return super(PostDTPHandlerMixin, self).close()


class PostDTPHandler(PostDTPHandlerMixin, _AsyncChatNewStyle, DTPHandler):
    pass


class TLS_PostDTPHandler(PostDTPHandlerMixin, TLS_DTPHandler):
    pass


class AccountAuthorizer(DummyAuthorizer):

    def __init__(self, accounts, http_basic_auth=False, backends=()):

        super(AccountAuthorizer, self).__init__()

        for username, password in accounts.items():
            self.add_user(username, password)

        if http_basic_auth:
            self._password_cache = {}
        else:
            self._password_cache = None

        self._backends = backends

    def add_user(self, username, password, perm='elw', msg_login='Login successful.', msg_quit='Goodbye.'):

        if self.has_user(username):
            raise ValueError('user %r already exists' % username)

        self._check_permissions(username, perm)

        homedir = username
        if not isinstance(homedir, unicode):
            homedir = homedir.decode('utf8')

        self.user_table[username] = {
            'pwd': str(password),
            'home': homedir,
            'perm': perm,
            'operms': {},
            'msg_login': str(msg_login),
            'msg_quit': str(msg_quit)
        }

    def _validate_with_url(self, username, password, url):
        try:
            parsed_url, connection = http_connection(url)
            if parsed_url.query:
                url_path = parsed_url.path + '?' + parsed_url.query
            else:
                url_path = parsed_url.path
            connection.putrequest('GET', url_path)
            credentials = base64.b64encode(b'%s:%s' % (username, password))
            connection.putheader('Authorization', 'Basic %s' % credentials)
            connection.endheaders()
            response = connection.getresponse()
            return response.status // 100 == 2
        except Exception as error:
            logger.error(error)
            return False

    def _validate_with_user_table(self, username, password):
        if self.has_user(username):
            stored_password = self.user_table[username]['pwd']
            if stored_password is not None:
                hashed_password = bcrypt.hashpw(password, stored_password)
                if hashed_password == stored_password:
                    return True
        return False

    def validate_authentication(self, username, password, handler):
        """
        Raises AuthenticationFailed if the supplied username and password
        are not valid credentials, else return None.

        """

        valid = self._validate_with_user_table(username, password)
        if not valid:
            for url in self._backends:
                valid = self._validate_with_url(username, password, url)
                if valid:
                    break

        if valid:
            if username not in self.user_table:
                self.add_user(username, password=None)
            if self._password_cache is not None:
                self._password_cache[username] = password
        else:
            raise AuthenticationFailed('Authentication failed.')


def read_configuration_file(path):
    config = {
        'accounts': {},
        'authentication_backend': [],
    }
    int_values = ('listen_port', 'passive_port_min', 'passive_port_max')
    try:
        with open(path) as conf_file:
            print 'Using configuration file %s' % path
            for line in conf_file:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split(':', 1)
                    value = value.strip()
                    if key == 'user':
                        name, password = value.split(':', 1)
                        config['accounts'][name] = password
                    elif key == 'http_basic_auth':
                        value = value.lower()
                        if value == 'true':
                            config[key] = True
                        elif value == 'false':
                            pass
                        else:
                            sys.stderr.write('Unknown value for %s: %s\n' % (key, value))
                            sys.exit(1)
                    elif key == 'authentication_backend':
                        config[key].append(value)
                    elif key == 'masquerade_address':
                        config[key] = socket.gethostbyname(value)
                    else:
                        if key in int_values:
                            value = int(value)
                        config[key] = value
    except IOError as error:
        if error.errno == errno.ENOENT:
            sys.stderr.write('Cannot find configuration file: %s\n' % path)
            sys.exit(1)
        raise

    urls = []
    for url in config.pop('authentication_backend'):
        if url.startswith('http://') or url.startswith('https://'):
            pass
        else:
            url = config['http_url'] + url
        urls.append(url)
    config['authentication_backends'] = urls

    return config


def start_ftp_server(http_url, accounts, authentication_backends=(),
                     ssl_cert_path=None, http_basic_auth=False,
                     listen_host=None, listen_port=None, listen_fd=None,
                     passive_port_min=None, passive_port_max=None,
                     masquerade_address=None):

    if ssl_cert_path:

        if not os.path.exists(ssl_cert_path):
            sys.stderr.write('Cannot find SSL certificate file: %s\n' % ssl_cert_path)
            sys.exit(2)

        handler = TLS_FTPHandler
        handler.dtp_handler = TLS_PostDTPHandler

        handler.certfile = ssl_cert_path
        handler.tls_control_required = True
        handler.tls_data_required = True

    else:

        handler = FTPHandler
        handler.dtp_handler = PostDTPHandler

    if passive_port_min and passive_port_max:
        handler.passive_ports = range(passive_port_min, passive_port_max + 1)

    if masquerade_address:
        handler.masquerade_address = masquerade_address

    handler.abstracted_fs = PostFS
    handler.authorizer = AccountAuthorizer(
        accounts=accounts,
        http_basic_auth=http_basic_auth,
        backends=authentication_backends,
    )
    handler.use_sendfile = False

    PostFS.post_file = MultipartPostFile
    PostFS.post_file.url = http_url

    if listen_fd not in (None, -1):
        listen_socket = socket.fromfd(listen_fd, socket.AF_UNIX, socket.SOCK_STREAM)
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen = listen_socket
    else:
        listen = (listen_host, listen_port)

    server = MultiprocessFTPServer(listen, handler)
    server.max_cons = 256
    server.max_cons_per_ip = 5
    server.serve_forever()
