from .simple_client import get, head, post, put, delete, connect, options, trace, patch
import sys

if len(sys.argv) == 1:
    url, method = 'localhost', 'GET'
elif len(sys.argv) == 2:
    url, method = sys.argv[1], 'GET'
elif len(sys.argv) > 2:
    url, method = sys.argv[1], sys.argv[2]

try: func = globals()[method.lower()]
except:
    print('Method not support!')
    sys.exit(1)

try: print(func(url,headers={'User-Agent':'Python GHTTP CLient'}).text)
except: print("Timeout")