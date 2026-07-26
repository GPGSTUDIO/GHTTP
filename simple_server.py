from .parsearg import parsearg
from .server import server
import subprocess
import json
import ssl
import os

def serve(IP='localhost',PORT=80,PATH='./',silent=False,keep_alive=False,SSL=False,ssl_cert='cert.pem',ssl_key='key.pem',onlyget=False):
    if SSL:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(ssl_cert, ssl_key)
    if PATH.endswith('/'):
        PATH = PATH[:-1]
    def wrapper(cl,addr,SSL,context,onlyget):
        if SSL:
            try: cl.conn = context.wrap_socket(cl.conn, server_side=True)
            except: pass
        cl.conn.settimeout(30.0)
        while True:
            try:
                question, data, headers = cl.read()
                if data == None:
                    if not silent:
                        print(f'[{':'.join([str(i) for i in addr])}]: Closed',flush=True)
                    cl.close()
                    break
                if question[0] == 'GET' or not onlyget:
                    cur_dir, args = parsearg(question[1])
                    while cur_dir.find('..') != -1:
                        cur_dir = cur_dir.replace( '..', '.')
                    directory = PATH+cur_dir
                    if not directory.endswith('/') and os.path.exists(directory) and os.path.isdir(directory):
                        directory += '/'
                    hasindex = False
                    if os.path.exists(directory) and os.path.isdir(directory):
                        files = os.listdir(directory)
                        for i in files:
                            if i == 'index.html' or i == 'index.py' or i == 'index.pyc':
                                hasindex = True
                    if hasindex:
                        if os.path.exists(f'{directory}index.py') or os.path.exists(f'{directory}index.pyc'):
                            try:
                                name = 'index.py'
                                if os.path.exists(f'{directory}index.pyc'):
                                    name = 'index.pyc'
                                output = subprocess.run([f'{os.path.abspath(directory)}/{name}', json.dumps(args), json.dumps(headers), question[0]],shell=True,stderr=subprocess.DEVNULL,stdout=subprocess.PIPE,input=data).stdout
                                dfheaders = {"Connection": "keep-alive" if keep_alive else "close"}
                                head, body = (b'', output[2:]) if output.startswith(b'\r\n') else output.split(b'\r\n\r\n',1)
                                shead = head.split(b'\r\n')
                                status = '200 OK'
                                for i in range(0,len(shead)):
                                    cur_head = shead[i].decode('latin-1')
                                    if cur_head.lower().startswith('status:'):
                                        status = cur_head[7:].strip()
                                    else:
                                        if ':' in cur_head:
                                            key, value = cur_head.split(':',1)
                                            value = value.strip()
                                            dfheaders[key] = value
                                cl.send(body,headers=dfheaders,status_code=status)
                                if not silent:
                                    print(f'[{':'.join([str(i) for i in addr])}]: {status} {cur_dir}',flush=True)
                            except:
                                cl.send(b'',status_code='500 Internal Server Error',headers={"Connection": "keep-alive" if keep_alive else "close"})
                                if not silent:
                                    print(f'[{':'.join([str(i) for i in addr])}]: 500 Internal Server Error {cur_dir}',flush=True)
                        elif os.path.exists(f'{directory}index.html'):
                            with open(f'{directory}index.html','rb') as f:
                                cl.send(f.read(),headers={"Content-Type": "text/html; charset=utf-8", "Connection": "keep-alive" if keep_alive else "close"})
                            if not silent:
                                print(f'[{':'.join([str(i) for i in addr])}]: 200 OK {cur_dir}',flush=True)
                    elif os.path.exists(directory):
                        if os.path.isdir(directory):
                            result = f'<h1>List of {cur_dir}</h1><a href="..">↩</a><br>'
                            for i in files:
                                result += f'<a href="./{i}">{i}</a><br>'
                            cl.send(result.encode(),headers={"Content-Type": "text/html; charset=utf-8", "Connection": "keep-alive" if keep_alive else "close"})
                            if not silent:
                                print(f'[{':'.join([str(i) for i in addr])}]: 200 OK {cur_dir}',flush=True)
                        else:
                            fileext = directory.rsplit('.',1)[-1]
                            if fileext == 'py' or fileext == 'pyc':
                                try:
                                    output = subprocess.run([f'{os.path.abspath(directory)}', json.dumps(args), json.dumps(headers), question[0]],shell=True,stderr=subprocess.DEVNULL,stdout=subprocess.PIPE,input=data).stdout
                                    dfheaders = {"Connection": "keep-alive" if keep_alive else "close"}
                                    head, body = (b'', output[2:]) if output.startswith(b'\r\n') else output.split(b'\r\n\r\n',1)
                                    shead = head.split(b'\r\n')
                                    status = '200 OK'
                                    for i in range(0,len(shead)):
                                        cur_head = shead[i].decode('latin-1')
                                        if cur_head.lower().startswith('status:'):
                                            status = cur_head[7:].strip()
                                        else:
                                            if ':' in cur_head:
                                                key, value = cur_head.split(':',1)
                                                value = value.strip()
                                                dfheaders[key] = value
                                    cl.send(body,headers=dfheaders,status_code=status)
                                    if not silent:
                                        print(f'[{':'.join([str(i) for i in addr])}]: {status} {cur_dir}',flush=True)
                                except:
                                    cl.send(b'',status_code='500 Internal Server Error',headers={"Connection": "keep-alive" if keep_alive else "close"})
                                    if not silent:
                                        print(f'[{':'.join([str(i) for i in addr])}]: 500 Internal Server Error {cur_dir}',flush=True)
                            else:
                                with open(directory,'rb') as f:
                                    cl.send(f.read(),{"Connection": "keep-alive" if keep_alive else "close"})
                                print(f'[{':'.join([str(i) for i in addr])}]: 200 OK {cur_dir}',flush=True)
                    else:
                        if not silent:
                            cl.send(b'',status_code='404 Not Found', headers={"Connection": "keep-alive" if keep_alive else "close"})
                        print(f'[{':'.join([str(i) for i in addr])}]: 404 Not Found {cur_dir}',flush=True)
                else:
                    if not silent:
                        cl.send(b'',status_code='400 Method Not Support', headers={"Connection": "keep-alive" if keep_alive else "close"})
                    print(f'[{':'.join([str(i) for i in addr])}]: 400 Method Not Support',flush=True)
            except:
                if not silent:
                    print(f'[{':'.join([str(i) for i in addr])}]: Error',flush=True)
                cl.close()
                break
    if not silent:
        print(f"Runned server at {IP}:{PORT}",flush=True)
    try:
        server(wrapper,IP,PORT,ARGS=(SSL,context if SSL else None,onlyget))
    except KeyboardInterrupt:
        print("KeyboardInterrupt, goodbye!")