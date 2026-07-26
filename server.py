from .transfer_encoding import read as read_encoding
import threading
import socket
def send(conn, ver, data, headers={}, status_code="200 OK", without_len=False, without_con=False, encoding='utf-8'):    if type(data)==str:
        data = data.encode(encoding=encoding)
    if type(status_code)==bytes:
        status_code = status_code.decode('latin-1')    close = False    result = f"HTTP/{ver} {status_code}\x0d\x0a"     for key, value in headers.items():        if key.lower()=='connection' and value.lower() == 'close':            close = True        result += f"{key}: {value}\x0d\x0a"
        if key.lower() == 'connection' and value.lower() == 'close':
            close = True
    if not without_con:        if not "\nconnection: " in result.lower():            result += f"Connection: close\x0d\x0a"            close = True    if not without_len:        if not "\ncontent-length: " in result.lower():            result += f"Content-Length: {len(data)}\x0d\x0a"    result += "\x0d\x0a"    data = result.encode() + data    conn.sendall(data)    if close:        conn.close()
def read(conn, binary_question=False, require_ver=True, auto_chunked=True):    try:        data = conn.recv(65500)        while b'\r\n\r\n' not in data:            chunk = conn.recv(65500)            if chunk == b'':                break            data += chunk    except: data = b''    if not data == b'':        data_split = data.find(b'\r\n\r\n')        header, dta = data[:data_split], data[data_split+4:]        headers = {}        h = header.split(b'\r\n')        if not require_ver:            question = h[0][:h[0].rfind(b' HTTP')].split(b' ',1)            question.append(None)        else:            question = h[0].split(b' ',1)            question = question[0], *question[1].rsplit(b' ',1)        for i in h[1:]:            key, value = i.split(b':',1)            key = key.decode(errors='replace')            value = value.lstrip(b' ').decode(errors='replace')            headers[key.lower()] = int(value) if value.isdigit() else value
        if 'transfer-encoding' in headers and auto_chunked:
            dta = read_encoding(s,dta,headers['transfer-encoding'])
        elif 'content-length' in headers:            toread = headers['content-length']            toread = int(toread) - len(dta)            while toread > 0:                chunk = conn.recv(toread if toread < 65500 else 65500)
                dta += chunk
                toread -= len(chunk)        if len(question) == 3:            if not binary_question:                question = question[0].decode(), question[1].decode(), question[2].decode()        else:            raise ValueError(f"Question is strange.. {question}")        return question, dta, headers    else:        return [None, None, None], None, {}

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

def read_raw(conn, data=None):
    try: return conn.recv(data)
    except: return None

def close(conn):
    try: conn.close()
    except: pass

def send_chunk(conn, data):
    if type(data)==bytes:
        conn.sendall(hex(len(data))[2:].encode() + b'\r\n' + data + b'\r\n')
    else:
        raise ValueError("data must be bytes!")

class tserver():
    def __init__(self, HOST='127.0.0.1', PORT=80, VER='1.1', precon=None, preaddr=None):
        if precon == None:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((HOST, PORT))
            s.listen()
            s.settimeout(5.0)
            self.s = s
        else:
            self.s = None
            self.conn = precon
            self.addr = preaddr
        self.ver = VER
    def accept(self, get_raw=False):
        if self.s == None:
            raise ValueError("While using precon, not allowed method accept!")
        else:
            conn, addr = self.s.accept()
            conn.settimeout(5.0)
            self.conn, self.addr = conn, addr
            if not get_raw:
                return addr
            else:
                return conn, addr
    def send(self, data, headers={}, status_code="200 OK", without_len=False, without_con=False):
        send(self.conn, self.ver, data, headers, status_code, without_len, without_con)
    def read(self, binary_question=False, require_ver=True, auto_chunked=True):
        return read(self.conn, binary_question, require_ver, auto_chunked)
    def send_raw(self, data):
        send_raw(self.conn, data)
    def send_chunk(self, data):
        send_chunk(self.conn, data)
    def read_chunk(self):
        return read_chunk(self.conn)
    def read_raw(self, count=None):
        return read_raw(self.conn, count)
    def close(self):
        close(self.conn)

def server(WRAPPER, HOST='127.0.0.1', PORT=80, VER='1.1', CUSTOM_SOCK=None, ARGS=(), TIMEOUT=0.5, BLOCK=True):
    if CUSTOM_SOCK is not None:
        try: serv.close()
        except: pass
        serv = CUSTOM_SOCK
    else:
        serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv.bind((HOST, PORT))
        serv.listen()
    if BLOCK:
        serv.settimeout(TIMEOUT)
    else:
        serv.setblocking(0)
    try:
        while True:
            try:
                conn, addr = serv.accept()
                s = tserver(HOST, PORT, VER, precon=conn, preaddr=addr)
                t = threading.Thread(target=WRAPPER, daemon=True, args=(s,addr,*ARGS))
                t.daemon = True
                t.start()
            except:
                pass
    except KeyboardInterrupt:
        raise KeyboardInterrupt()