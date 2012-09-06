# -*- coding: utf-8 -*-
'''
Copyright (c) 2011-2012 Skydark. All rights reserved.

Skydark Chen <skydark2 at gmail>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

__author__ = 'Skydark Chen'
__license__ = 'GPLv2'


import os

from ons import ONScripterError
from utils import cd_once, Struct
from portable import bytechr, py3k, decode, UEMPTY


DEFAULT_SCRIPT_ENCODING = 'GBK'


class ONScripterLabel(Struct):
    name = b''
    start_line = -1
    start_address = -1


class ONSHandlerError(ONScripterError):
    pass


class ONSHandler(object):
    def __init__(self, path, encoding=None):
        self.encoding = encoding or DEFAULT_SCRIPT_ENCODING
        self.global_variable_border = 200
        self.path = path
        self.buf = ''
        self.mode = 640
        self.label_info = []
        if os.path.isdir(path):
            cd_once(path, self.read)
        elif os.path.isfile(path):
            self.read(path)
        else:
            raise ONSHandlerError('Unknown path: %s' % path)

    def get_script(self):
        ret = UEMPTY
        try:
            ret = decode(self.buf, self.encoding)
        except UnicodeDecodeError:
            encodings = ['GB18030', 'SHIFT-JIS', 'UTF-8']
            if os.path.isfile(self.path):
                encodings.extend(['UTF-16LE', 'BIG5'])
            if self.encoding in encodings:
                encodings.remove(self.encoding)
            for encoding in encodings:
                try:
                    ret = decode(self.buf, encoding)
                    self.encoding = encoding
                    break
                except UnicodeDecodeError:
                    pass
        if ret:
            return ret
        raise ONSHandlerError('Can not decode script')

    def read(self, file_=None):
        buf = ''
        if file_:
            buf = open(file_, 'rb').read()
        else:
            for start in ('0.txt', '00.txt', 'nscript.dat'):
                try:
                    buf = open(start, 'rb').read()
                    break
                except IOError:
                    pass
            else:
                raise ONSHandlerError('No script found!')
            if start == 'nscript.dat':
                buf = b''.join(bytechr(ord(c) ^ 0x84) for c in buf)
            else:
                bufs = [buf]
                for i in range(1, 100):
                    try:
                        text = open('%d.txt' % i, 'rb').read()
                    except IOError:
                        if i >= 10:
                            continue
                        try:
                            text = open('%02d.txt' % i, 'rb').read()
                        except IOError:
                            continue
                    bufs.append(text)
                buf = b'\n'.join(bufs)
        buf = buf.replace(b'\r\n', b'\n').replace(b'\r', b'\n')

        # try:
        #     buf = buf.decode(self.encoding)
        # except UnicodeDecodeError:
        #     raise ONSHandlerError(
        #             'Decode script with %s failed!' % self.encoding)

        p = 1
        while buf[0:1] == b';':
            if buf[p:p+4] == b'mode':
                try:
                    self.mode = int(buf[p+4:p+7])
                except ValueError:
                    pass
                p += 7
            elif buf[p:p+5] == b'value':
                p += 5
                while buf[p:p+1] in b'\t \n':
                    p += 1
                q = p
                while buf[p:p+1].isdigit():
                    p += 1
                self.global_variable_border = int(buf[q:p])
            else:
                break
            if buf[p:p+1] != b',':
                break
            p += 1

        self.buf = buf
        #open('resultbuf.txt', 'wb').write(buf)
        self.readLabel()

    def readLabel(self):
        state, label, lno = 'newline', b'', 0
        label_info = []
        for i, c in enumerate(self.buf):
            if py3k:
                c = bytechr(c)
            if state == 'label':
                c = c.upper()
                if c.isalnum() or c == b'_':
                    label += c
                else:
                    assert self.buf[i-len(label)-1:i-len(label)] == b'*'
                    state = 'newline' if c == b'\n' else 'ready'
                    label_info.append(ONScripterLabel(
                        name=label,
                        start_line=lno,
                        start_address=i-len(label)-1,
                        ))
                    label = b''
                    if c == b'\n':
                        lno += 1
                continue
            elif state == 'newline':
                if c in b'\t ':
                    continue
                if c == b'*':
                    state, label = 'label', b''
                    continue
                state = 'ready'
            if c == b'\n':
                state, lno = 'newline', lno + 1
        self.label_info = label_info
        # print([c.name for c in label_info])

    def getLineStringByAddress(self, addr):
        return self.buf[addr:self.buf.find(b'\n', addr)]

    def getLabelByLine(self, line):
        for i, label in enumerate(self.label_info):
            if label.start_line > line:
                return self.label_info[i-1]
        return self.label_info[-1]

    def getLabelByAddress(self, address):
        for i, label in enumerate(self.label_info):
            if label.start_address > address:
                return self.label_info[i-1]
        return self.label_info[-1]

    def getAddressByLine(self, line):
        label = self.getLabelByLine(line)
        l = line - label.start_line
        addr = label.start_address
        buf = self.buf
        length = len(buf)
        while l > 0:
            while addr < length and buf[addr:addr+1] != b'\n':
                addr += 1
            addr += 1
            l -= 1
        return addr

    def getLineByAddress(self, address, relative=True):
        label = self.getLabelByAddress(address)
        addr = label.start_address
        line = 0 if relative else label.start_line
        buf = self.buf
        if address >= len(buf):
            raise ONSHandlerError('Script address %s overflow!' % address)
        while address > addr:
            if buf[addr:addr+1] == b'\n':
                line += 1
            addr += 1
        return line

    def findLabel(self, name):
        name = name.upper()
        for i, label in enumerate(self.label_info):
            if label.name == name:
                return i, label
        raise ONSHandlerError('No label %s found!' % name)
