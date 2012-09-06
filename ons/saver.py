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


import logging

from ons import ONScripterError
from portable import b_ord, chr_join

ENCODING = 'gb18030'

_logger = logging.getLogger('ons.saver')
_logger.addHandler(logging.StreamHandler())
# _logger.setLevel(logging.DEBUG)
_logger.setLevel(logging.ERROR)


def printd(s):
    _logger.debug(s)


class ONSSaverError(ONScripterError):
    pass


class ONSSaver(object):
    MAX_SPRITE_NUM = 1000
    MAX_SPRITE2_NUM = 256
    MAX_PARAM_NUM = 100
    MAX_EFFECT_NUM = 256

    def __init__(self, handler):
        self.handler = handler
        self.code = b''
        self.length = 0
        self.p = 0

    def reset(self):
        self.p = 0
        self.stack_offset = None
        self.num_nest = 0
        self.nest_info = []
        self.current_offset = (None, )

    def readInt(self, count=1):
        ret = []
        p, code = self.p, self.code
        for i in range(count):
            n = b_ord(code[p]) + (b_ord(code[p+1])<<8) + \
                (b_ord(code[p+2])<<16) + (b_ord(code[p+3])<<24)
            if b_ord(code[p+3]) > 8:
                n -= (2 << 31)
            ret.append(n)
            p += 4
        self.p = p
        return ret if len(ret) != 1 else ret[0]

    def readChar(self, count=1):
        cnt = 0
        ret = []
        code, l, p = self.code, self.length, self.p
        while cnt < count and p < l:
            ret.append(code[p:p+1])
            cnt += 1
            p += 1
        self.p = p
        return b''.join(ret)

    def readStr(self, count=1):
        ret = []
        code = self.code
        for i in range(count):
            pos = code.find(b'\x00', self.p)
            assert pos >= 0
            ret.append(code[self.p:pos])
            self.p = pos + 1
        return ret if len(ret) != 1 else ret[0]

    def readBool(self, count=1):
        b = self.readInt(count)
        if isinstance(b, list):
            assert all(x in (0, 1) for x in b)
        else:
            assert b in (0, 1)
        return b

    def load(self, savedata):
        self.reset()
        self.code = savedata
        self.length = len(savedata)
        readChar = self.readChar
        assert readChar(3) == b'ONS'
        file_version = ord(readChar()) * 100 + ord(readChar())
        printd('Save version: %s' % file_version)
        self.doPreCheck(file_version)
        self.getStackOffset()
        self.doPostCheck(file_version)
        self.getCurrentLine()

    def doPreCheck(self, file_version):
        readInt, readChar, readStr, readBool =\
            self.readInt, self.readChar, self.readStr, self.readBool
        assert readInt() == 1
        readBool(), readBool()  # bold, shadow
        assert readInt() == 0
        readBool()  # rmode
        readInt(3)  # font rgb
        readStr(2)  # cursor
        readInt(2), readStr()  # window effect, effect_image
        readInt(8)  # font
        readChar(3)  # window color
        readChar()  # font transparent
        readInt()  # waittime
        readInt(4), readStr()  # animation info, animation image
        readInt(2)  # absflag
        readInt(4)  # cursor info
        readStr()  # bgimage
        readStr(3), readInt(3), readInt(3)  # tachi image, tachi x, tachi y
        assert readInt(3) == [0] * 3
        if file_version >= 203:
            assert readInt(3) == [-1] * 3
        for i in range(self.MAX_SPRITE_NUM):
            #ai image, xy, visible, cell, trans
            sprite_info = [
                    readStr(), readInt(), readInt(), readBool(), readInt()]
            if file_version >= 203:
                sprite_info.append(readInt())  # trans
            # if sprite_info[0]: print i, sprite_info
        self.readVariables(0, self.handler.global_variable_border)

    def doPostCheck(self, file_version):
        readInt, readChar, readStr, readBool =\
            self.readInt, self.readChar, self.readStr, self.readBool
        readBool(), readInt(3)  # monocro & color
        readInt()  # nega mode
        readStr(2)  # midi, wave
        readInt()  # cdtrack
        readBool(5)  # playloop, waveloop, playonce, bgmloop, mp3loop
        readStr()  # musicname
        readBool()  # erase text window
        assert readInt() == 1
        for i in range(self.MAX_PARAM_NUM):
            j = readInt()
            if j:
                readInt(5)  # ai:x,y,max_w,h,max_param
                readChar(3)  # color
                assert ord(readChar()) == 0
            else:
                assert readInt(6) == [-1, 0, 0, 0, 0, 0]
        for i in range(self.MAX_PARAM_NUM):
            j = readInt()
            readInt(5)  # FIXME
        assert readInt(3) == [1, 0, 1]
        readStr()  # btndef image
        if file_version >= 202:
            self.readArrayVariable()  # <TODO>read array variables
        # <TODO>
        return

    def readArrayVariable(self):
        pass

    def getStackOffset(self):
        readInt = self.readInt
        num_nest = readInt()
        nest_info = []
        self.stack_offset = self.p
        if num_nest > 0:
            ons = self.handler
            printd('nested info: %s' % num_nest)
            self.p += (num_nest - 1) * 4
            while num_nest > 0:
                i = readInt()
                if i > 0:
                    nest_info.append(('label', i))
                    self.p -= 8
                    num_nest -= 1
                else:
                    self.p -= 16
                    # info_var_no, info_to, info_step = readInt(3)
                    nest_info.append((('for', readInt(3)), -i, ))
                    self.p -= 16
                    num_nest -= 4
            num_nest = readInt()
            self.p += num_nest * 4
            self.num_nest = num_nest
            self.nest_info = [0] * len(nest_info)
            nest_info.reverse()
            for j, (type_, addr) in enumerate(nest_info):
                label = ons.getLabelByAddress(addr)
                line = ons.getLineByAddress(addr, relative=False)
                line_offset = line - label.start_line
                line_start_addr = ons.getAddressByLine(line)
                self.nest_info[j] = (
                        type_, addr, label, line, line_offset, line_start_addr)
                # try:
                #      print(type_, addr,
                #              ons.buf[addr:ons.buf.find('\n', addr+1)]
                #              .decode(ENCODING))
                # except UnicodeDecodeError:
                #     print(type_, addr)
                # print(label.name)

    def getCurrentLine(self):
        p = self.length - 1
        code = self.code
        handler = self.handler
        if code[p:p+1] == b'*':
            assert code[p-1:p] == b'"'
            p -= 2
            while code[p:p+1] != b'"':
                p -= 1
            p -= 1
        self.p = p - 7
        line, current_inline_offset = self.readInt(2)
        label = handler.getLabelByLine(line)
        line_offset = line - label.start_line
        line_start_addr = handler.getAddressByLine(line)
        addr = line_start_addr
        for i in range(current_inline_offset):
            while handler.buf[addr:addr+1] != ':':
                addr += 1
            addr += 1
        self.current_offset = (
            self.p, current_inline_offset,
            addr, label, line, line_offset, line_start_addr
            )
        printd('savestr: %s' % code[self.p:].decode(ENCODING))

    def readVariables(self, from_, to_):
        printd('Variable size: %s' % to_)
        for i in range(from_, to_):
            k, s = self.readInt(), self.readStr()
            if k != 0:
                printd('Integer variable #%s: %s' %(i, k))
            if s:
                printd('String variable #%s: %s' %(i, s))

    def writeInt(self, i):
        if i < 0:
            i += (2 << 31)
        a, b = i % 256, i // 256
        b, c = b % 256, b // 256
        c, d = c % 256, c // 256
        assert 0 <= d < 256
        return chr_join([a, b, c, d])

    def save(self):
        raise NotImplementedError('Not Implemented for generating savedata!')
