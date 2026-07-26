def _read_chunked(data, full_data, s):
    header_end = data.find(b'\r\n')
    if header_end == -1:
        return data, full_data, False
    header = data[:header_end]
    try: toread = int(header.decode(), 16)
    except: pass
    if toread == 0:
        return b'', full_data, True
    rest = data[header_end + 2:]
    while len(rest) < toread + 2:
        rest += s.recv(min(65500, toread + 2 - len(rest)))
    full_data += rest[:toread]
    return rest[toread + 2:], full_data, False

def read(s, data=b'', encoding='chunked'):
    if encoding == 'chunked':
        full_data = b''
        while True:
            header_end = data.find(b'\r\n')
            if header_end != -1:
                data, full_data, done = _read_chunked(data, full_data, s)
                if done:
                    return full_data
            else:
                data += s.recv(65500)