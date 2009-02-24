# Module:   webob
# Date:     13th September 2007
# Author:   James Mills, prologic at shortcircuit dot net dot au

"""Web Objects

This module implements the Request and Response objects.
"""


import os
import stat
from cStringIO import StringIO
from time import strftime, time
from Cookie import SimpleCookie

from headers import Headers
from utils import compressBuf
from constants import BUFFER_SIZE, SERVER_VERSION

class Host(object):
    """An internet address.

    name should be the client's host name. If not available (because no DNS
    lookup is performed), the IP address should be used instead.
    """

    ip = "0.0.0.0"
    port = 80
    name = "unknown.tld"

    def __init__(self, ip, port, name=None):
        self.ip = ip
        self.port = port
        if name is None:
            name = ip
            self.name = name

    def __repr__(self):
        return "Host(%r, %r, %r)" % (self.ip, self.port, self.name)

class Request(object):
    """Request(method, path, protocol, qa, headers) -> new HTTP Request object

    Request object that holds an incoming request.
    """

    server = None
    script_name = ""
    scheme = "http"
    server_protocol = (1, 1)
    request_line = ""
    protocol = (1, 1)
    login = None
    local_host = Host("127.0.0.1", 80)
    remote_host = Host("127.0.0.1", 1111)

    def __init__(self, method, path, protocol, qs):
        "initializes x; see x.__class__.__doc__ for signature"

        self._headers = None

        self.method = method
        self.path = self.path_info = path
        self.protocol = protocol
        self.qs = self.query_string = qs
        self.cookie = SimpleCookie()

        self.body = StringIO()

    def _getHeaders(self):
        return self._headers

    def _setHeaders(self, headers):
        self._headers = headers
        if "Cookie" in self.headers:
            self.cookie.load(self.headers["Cookie"])

    headers = property(_getHeaders, _setHeaders)

    def __repr__(self):
        protocol = "HTTP/%d.%d" % self.protocol
        return "<Request %s %s %s>" % (self.method, self.path, protocol)

class Response(object):
    """Response(sock) -> new Response object

    A Response object that holds the response to
    send back to the client. This ensure that the correct data
    is sent in the correct order.
    """

    request = None

    def __init__(self, sock):
        "initializes x; see x.__class__.__doc__ for signature"

        self.sock = sock
        self.clear()

    def __repr__(self):
        return "<Response %s %s (%d)>" % (
                self.status,
                self.headers["Content-Type"],
                (len(self.body) if type(self.body) == str else 0))
    
    def __str__(self):
        status = self.status
        headers = self.headers
        body = self.process()
        protocol = "HTTP/%d.%d" % self.request.server_protocol
        return "%s %s\r\n%s%s" % (protocol, status, headers, body or "")

    def clear(self):
        self.done = False
        self.close = False
        
        self.headers = Headers([
            ("Server", SERVER_VERSION),
            ("Date", strftime("%a, %d %b %Y %H:%M:%S %Z"))])
        self.cookie = SimpleCookie()

        self.stream = False
        self.gzip = False
        self.body = ""
        self.time = time()
        self.status = "200 OK"

    def process(self):
        for k, v in self.cookie.iteritems():
            self.headers.add_header("Set-Cookie", v.OutputString())

        if type(self.body) == file:
            cType = self.headers.get("Content-Type", "application/octet-stream")
            if self.gzip:
                self.body = compressBuf(self.body.read())
                self.headers["Content-Encoding"] = "gzip"
                self.body.seek(0, 2)
                cLen = self.body.tell()
                self.body.seek(0)
            else:
                cLen = os.fstat(self.body.fileno())[stat.ST_SIZE]

            if cLen > BUFFER_SIZE:
                body = self.body.read(BUFFER_SIZE)
                self.stream = True
            else:
                body = self.body.read()
        elif type(self.body) == str:
            body = self.body
            if self.gzip:
                body = compressBuf(body).getvalue()
                self.headers["Content-Encoding"] = "gzip"
            cLen = len(body)
            cType = self.headers.get("Content-Type", "text/html")
        else:
            body = ""
            cLen = 0
            cType = "text/plain"

        self.headers["Content-Type"] = cType
        self.headers["Content-Length"] = str(cLen)

        return body
