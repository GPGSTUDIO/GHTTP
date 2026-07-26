from .simple_server import serve
import sys

if len(sys.argv) == 1:
    url, path = '0.0.0.0:80', './'
elif len(sys.argv) == 2:
    url, path = sys.argv[1], './'
elif len(sys.argv) > 2:
    url, path = sys.argv[1], sys.argv[2]

if url.isdigit():
    ip, port = '0.0.0.0', url
elif ':' in url:
    ip, port = url.rsplit(':',1)
else:
    ip, port = url, 80

try: serve(ip,int(port),path,keep_alive=True)
except KeyboardInterrupt:
    print("KeyboardInterrupt, exiting")