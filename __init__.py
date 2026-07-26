"""
GHTTP By GPGStudio created for easy work with http,
See everything in "README"
"""

from .parsearg import parsearg, parse, unparse
from .server import server, tserver
from .client import client
from .transfer_encoding import read as transfer_encoding
from .simple_client import get, head, post, put, delete, connect, options, trace, patch, Session, parseurl
from .simple_server import serve

__all__ = ['parsearg','parse','unparse','server','tserver','client','transfer_encoding','get','head','post','put','delete','connect','options','trace','patch','Session','serve','parseurl']
__version__ = '0.1.1'