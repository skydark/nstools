# -*- coding: utf-8 -*-

import sys

py = sys.version_info
py3k = py >= (3, 0, 0)

default_encoding = sys.getfilesystemencoding()
if default_encoding.lower() == 'ascii':
    default_encoding = 'utf-8'

from codecs import open

if py3k:
    is_bytes = lambda s: isinstance(s, bytes)
    is_unicode = lambda s: isinstance(s, str)
    is_str = lambda s: isinstance(s, (bytes, str))
    encode = lambda s, encoding=None: bytes(s, encoding or default_encoding)
    unistr = str
    bytechr = lambda c: bytes(chr(c), 'charmap')
    chr = chr
    UEMPTY = ''
    b_ord = lambda c: c
    chr_join = lambda l: bytes(l)
else:
    is_bytes = lambda s: isinstance(s, str)
    is_unicode = lambda s: isinstance(s, unicode)
    is_str = lambda s: isinstance(s, basestring)
    encode = lambda s, encoding=None: s.encode(encoding or default_encoding)
    unistr = unicode
    bytechr = chr
    chr = unichr
    UEMPTY = ''.decode('utf-8')
    b_ord = lambda c: ord(c)
    chr_join = lambda l: b''.join(bytechr(c) for c in l)

decode = lambda s, encoding=None: s.decode(encoding or default_encoding)

to_bytes = lambda s, encoding=None: \
    encode(s, encoding) if is_unicode(s) else s
to_unicode = lambda s, encoding=None: \
    s if is_unicode(s) else decode(s, encoding)
B = to_bytes
U = lambda s: to_bytes(s).decode('raw_unicode_escape')


if py3k:
    from urllib.request import urlopen, Request
else:
    from urllib2 import urlopen, Request

if py3k:
    from io import BytesIO as StringIO
else:
    from cStringIO import StringIO

if py3k:
    import tkinter
    import tkinter.filedialog as tkFileDialog
    import tkinter.messagebox as tkMessageBox
else:
    import Tkinter as tkinter
    import tkFileDialog
    import tkMessageBox
