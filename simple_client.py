from .parsearg import parse
from .client import client
import json as json_mod
import socket
import ssl

class _clresponse:
    def __init__(self,data,code,text,headers):
        self.binary = data
        self.status = code
        self.text_status = text
        self.headers = headers
    @property
    def text(self):
        encoding = 'utf-8'
        if 'content-type' in self.headers:
            import re
            match = re.search(r'charset=([^\s;]+)', self.headers['content-type'])
            if match:
                encoding = match.group(1)
        try:
            return self.binary.decode(encoding)
        except:
            return self.binary.decode('latin-1')
    def json(self):
        if not hasattr(self, '_json_cache'):
            try:
                self._json_cache = json_mod.loads(self.text)
            except:
                self._json_cache = None
        return self._json_cache
    @property
    def ok(self):
        return 200 <= self.status < 400
    def raise_for_status(self):
        if not self.ok:
            raise Exception(f"HTTP {self.status} {self.text_status}")

def _send_with_retry(s, method, path, headers, payload, ip, port, getsock, max_retries=2):
    for attempt in range(max_retries):
        try:
            s.send(method, path, headers=headers, without_len=True, data=payload)
            return s
        except Exception:
            if attempt == max_retries - 1:
                raise ValueError('Timeout')
            s.close()
            if getsock:
                s = client()
                s.connect(ip, port)
            else:
                s = client()
                s.connect(ip, port)
    return s

def _receive_with_retry(s, ip, port, getsock, max_retries=2):
    for attempt in range(max_retries):
        try:
            answer, data, headers = s.read()
            return answer, data, headers
        except Exception:
            if attempt == max_retries - 1:
                raise ValueError('Timeout')
            s.close()
            if getsock:
                s = client()
                s.connect(ip, port)
            else:
                s = client()
                s.connect(ip, port)
    return None, None, None

def parseurl(url):
    https = False
    if 'https://' in url:
        https = True
    address = url.replace('http://', '').replace('https://', '')
    if '/' in address:
        host, rest = address.split('/', 1)
        path = '/' + rest
    else:
        host = address
        path = '/'
    if '?' in host:
        host, query = host.split('?', 1)
        if path == '/':
            path = '/?' + query
        else:
            path = path + '?' + query
    ip, port = host.split(':', 1) if len(host.split(':', 1)) == 2 else (host, 80 if not https else 443)
    port = int(port)
    return ip, port, https, path

def _get(url, data, json, headers, params, method, sock=None, close=True, getsock=False, usehost=True, safe='1234567890-+_.~qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'):
    ip, port, https, path = parseurl(url)
    arlpar = '?' in path, '=' in path, path.endswith('&')
    first = True
    for key, value in params.items():
        if arlpar[2]:
            pass
        elif arlpar[1]:
            path += '&'
        elif arlpar[0]:
            pass
        else:
            path += '?' if first else '&'
        path += f'{key}={parse(value,safe=safe)}'
        arlpar = False, False, False
        first = False
    if data is not None:
        payload = data
    elif json is not None:
        payload = json_mod.dumps(json).encode()
    else:
        payload = b''
    dfheaders = {}
    if usehost:
        dfheaders['Host'] = ip
    if not payload == b'':
        dfheaders['Content-Length'] = str(len(payload))
    dfheaders.update(headers)
    if sock is None:
        s = client()
        if https:
            context = ssl.create_default_context()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssl_sock = context.wrap_socket(sock, server_hostname=ip)
            s.connect(ip, port, ssl_sock)
        else:
            s.connect(ip, port)
    else:
        s = sock
    s = _send_with_retry(s, method, path, dfheaders, payload, ip, port, getsock)
    answer, data, headers = _receive_with_retry(s, ip, port, getsock)
    if data is None:
        s.close()
        s = client()
        s.connect(ip, port)
        s = _send_with_retry(s, method, path, dfheaders, payload, ip, port, getsock)
        answer, data, headers = _receive_with_retry(s, ip, port, getsock)
        if data is None:
            raise ValueError('Timeout')
    status = answer[1].split(' ', 1)
    try: status_code = int(status[0])
    except: status_code = status[0]
    status_text = status[1] if len(status) == 2 else None
    if close:
        s.close()
    response = _clresponse(data, status_code, status_text, headers)
    return (s, response) if getsock else response

def get(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'GET', usehost=usehost)

def post(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'POST', usehost=usehost)

def delete(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'DELETE', usehost=usehost)

def put(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'PUT', usehost=usehost)

def head(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'HEAD', usehost=usehost)

def connect(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'CONNECT', usehost=usehost)

def options(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'OPTIONS', usehost=usehost)

def trace(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'TRACE', usehost=usehost)

def patch(url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
    return _get(url,data,json,headers,params,'PATCH', usehost=usehost)

class Session:
    def __init__(self):
        self.s = None
        self.url = None

    def reload(self):
        self.close()
        self.s = None
        self.url = None

    def close(self):
        try: self.s.close()
        except: pass

    def check_url(self, url):
        ip, port, https, path = parseurl(url)
        _url = f'{ip}:{port}'
        if not _url == self.url:
            self.url = _url
            self.reload()

    def get(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'GET',self.s,False,True,usehost)
        return answer

    def post(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'POST',self.s,False,True,usehost)
        return answer

    def delete(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'DELETE',self.s,False,True,usehost)
        return answer

    def put(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'PUT',self.s,False,True,usehost)
        return answer

    def head(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'HEAD',self.s,False,True,usehost)
        return answer

    def connect(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'CONNECT',self.s,False,True,usehost)
        return answer

    def options(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'OPTIONS',self.s,False,True,usehost)
        return answer

    def trace(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'TRACE',self.s,False,True,usehost)
        return answer

    def patch(self,url='localhost:80', data=None, json=None, headers={}, params={}, usehost=True):
        self.check_url(url)
        self.s, answer = _get(url,data,json,headers,params,'PATCH',self.s,False,True,usehost)
        return answer