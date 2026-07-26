from .transfer_encoding import read as read_encoding
import socket

def read(s, auto_chunked=True):
    try:
        data = s.recv(65500)
        while b'\r\n\r\n' not in data:
            chunk = s.recv(65500)
            if chunk == b'':
                break
            data += chunk
    except: data = b''
    if not data == b'':
        data_split = data.find(b'\r\n\r\n')
        header, dta = data[:data_split], data[data_split+4:]
        headers = {}
        h = header.split(b'\r\n')
        answer = h[0].split(b' ',1)
        answer = answer[0].decode(), answer[1].decode()
        for i in h[1:]:
            key, value = i.split(b':',1)
            key = key.decode(errors='replace')
            value = value.lstrip(b' ').decode(errors='replace')
            headers[key.lower()] = int(value) if value.isdigit() else value
        if 'transfer-encoding' in headers and auto_chunked:
            dta = read_encoding(s,dta,headers['transfer-encoding'])
        elif 'content-length' in headers:
            toread = headers['content-length']
            toread = int(toread) - len(dta)
            while toread > 0:
                chunk = s.recv(toread if toread < 65500 else 65500)
                dta += chunk
                toread -= len(chunk)
        else:
            s.settimeout(0.5)
            while True:
                try: chunk = s.recv(65500)
                except: break
                if chunk == b'':
                    break
                dta += chunk
            s.settimeout(5.0)
        return answer, dta, headers
    else:
        return [None, None], None, {}

def send(s, method='GET', path='/', ver='1.1', data=b'', headers={}, without_len=False, encoding='utf-8'):
    if type(data)==str:
        data = data.encode(encoding=encoding)    result = f"{method} {path} HTTP/{ver}\x0d\x0a" 
    for key, value in headers.items():        result += f"{key}: {value}\x0d\x0a"    if not without_len:        if not "\ncontent-length: " in result.lower():            result += f"Content-Length: {len(data)}\x0d\x0a"    result += "\x0d\x0a"    data = result.encode() + data    s.sendall(data)

def send_raw(conn, data):
    if type(data)==bytes:
        conn.sendall(data)
    else:
        raise ValueError("data must be bytes!")

def read_chunk(conn):
    try:
        chunk_size_hex = b''
        while True:
            char = conn.recv(1)
            if not char:
                return None
            if char == b'\n':
                break
            chunk_size_hex += char
        if chunk_size_hex.endswith(b'\r'):
            chunk_size_hex = chunk_size_hex[:-1]
        try:
            chunk_size = int(chunk_size_hex, 16)
        except ValueError:
            return None
        if chunk_size == 0:
            conn.recv(2)
            return (b'', 0)
        data = b''
        while len(data) < chunk_size:
            remaining = chunk_size - len(data)
            chunk = conn.recv(min(remaining, 8192))
            if not chunk:
                return None
            data += chunk
        conn.recv(2)
        return data, chunk_size
    except Exception:
        return None, None

def send_chunk(conn, data):
    if type(data)==bytes:
        conn.sendall(hex(len(data))[2:].encode() + b'\r\n' + data + b'\r\n')
    else:
        raise ValueError("data must be bytes!")

def read_raw(s, data=None):
    try: return s.recv(data)
    except: return None

def close(s):
    try: s.close()
    except: pass

class client:
    def __init__(self, VER='1.1'):
        self.ver = VER
        self.s = None
        pass
    def connect(self, IP='localhost', PORT=80, CUSTOM_SOCK=None):
        try: self.s.close()
        except: pass
        try:
            if CUSTOM_SOCK is None:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            else:
                s = CUSTOM_SOCK
            s.settimeout(5.0)
            s.connect((IP,PORT))
            self.s = s
        except: pass
    def read(self, auto_chunked=True):
        return read(self.s, auto_chunked)
    def send(self, method='GET', path='/', data=b'', headers={}, without_len=False):
        send(self.s, method, path, self.ver, data, headers, without_len)
    def send_raw(self, data):
        send_raw(self.s, data)
    def send_chunk(self, data):
        send_chunk(self.s, data)
    def read_chunk(self):
        return read_chunk(self.s)
    def read_raw(self, data=None):
        return read_raw(self.s, data)
    def close(self):
        close(self.s)
    