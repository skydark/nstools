#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Convert GBK nscripter dat to SHIFT-JIS version
Usage: gbk2sjis.py [options] origin_file output_file=['./out.txt']
    or gbk2sjis.py [options] origin_directory output_file=['./out.txt']

Options:
  -h --help            show this help
  -m --method METHOD   set method for missing characters, auto/manual [default: auto]

"""

from os import path
import sys
import codecs
import random

from docopt import docopt

from ons.handler import ONSHandler
from portable import decode, encode, chr, UEMPTY, py3k


def help():
    exit(__doc__.strip())


def hzconvert(text, from_, to_, method='auto', chardict=None):
    assert from_ == 'gbk' and to_ == 'sjis' and method == 'auto'

    from zhtools import chconv, xpinyin
    cdict = chconv.Chinese2Kanji_Table
    for k, v in chardict.items():
        try:
            encode(v, 'SHIFT-JIS')
            cdict[ord(k)] = ord(v)
        except UnicodeEncodeError:
            pass

    xpy = xpinyin.Pinyin()
    guess_chars = set()
    except_chars = set()

    def gbk_to_sjis(exc):
        if not isinstance(exc, UnicodeEncodeError):
            raise exc
        newpos = exc.end
        char = exc.object[exc.start:exc.end]
        c = ord(char)
        if c in cdict:
            # print('%s: %s matched!' %(char, cdict[c]))
            return chr(cdict[c]), newpos
        pinyin = xpy.get_pinyin(char)
        ok = []
        if pinyin:
            for newchar in xpy.py2hz(pinyin):
                try:
                    encode(newchar, 'SHIFT-JIS')
                    ok.append(newchar)
                except UnicodeEncodeError:
                    pass
            for newchar in xpy.py2hz(pinyin[:-1]):
                try:
                    encode(newchar, 'SHIFT-JIS')
                    ok.append(newchar)
                except UnicodeEncodeError:
                    pass
        if ok:
            newchar = random.choice(ok)
            cdict[c] = ord(newchar)
            guess_chars.add(c)
            # print('%s: %s' %(char, ','.join(ok)))
            return newchar, newpos
        except_chars.add(c)
        # print('Can not encode %s, ignore' % char)
        return ' ' * (newpos - exc.start), newpos

    codecs.register_error('gbk_to_sjis', gbk_to_sjis)
    # from zhtools import langconv
    # text = langconv.Converter('zh-hant').convert(text)
    try:
        text = text.encode('SHIFT-JIS', errors='gbk_to_sjis')
    except UnicodeError as exc:
        char = exc.object[exc.start:exc.end]
        print(char)
        raise
    print('These chars cannot encode to shift-jis:')
    if py3k:
        print(''.join(chr(c) for c in except_chars))
    else:
        print(encode(UEMPTY.join(chr(c) for c in except_chars)))
    print('These chars can be guessed by pinyin:')
    if py3k:
        print(''.join(chr(c) for c in guess_chars))
    else:
        print(encode(UEMPTY.join(chr(c) for c in guess_chars)))
    return text


def read_char_dict(data_path, encoding=None):
    chardict = {}
    try:
        buf = open(data_path, 'rb').read()
        buf = decode(buf, encoding)
        for data in buf.splitlines():
            k, v = data.strip().split(' ', 1)
            chardict[k] = v
    except Exception as e:
        print(e)
    else:
        print('Success load char dict: %s, %s' % (data_path, len(chardict)))
    return chardict


def main(args, gui=True):
    if len(args) <= 1 and gui:
        # Show GUI
        from portable import tkFileDialog

        def file_or_directory(p):
            filename = path.basename(p)
            dirname = path.dirname(p)
            if filename == 'nscript.dat':
                return dirname
            base, ext = path.splitext(filename)
            if ext != '.txt':
                return dirname
            if base.isdigit() and 0 <= int(base) < 100:
                return dirname
            return p

        in_path = tkFileDialog.askopenfilename(title='请选择脚本文件')
        in_path = file_or_directory(in_path)
        print('in_path: ' + in_path)
        if not in_path:
            exit()
        out_path = tkFileDialog.asksaveasfilename(title='请选择要保存的文件名')
        if not out_path:
            exit()
        method = 'auto'
    else:
        options, arguments = docopt(__doc__)
        if len(arguments) == 1:
            in_path = arguments[0]
            out_path = './out.txt'
        elif len(arguments) != 2:
            help()
        else:
            in_path = arguments[0]
            out_path = arguments[1]
        method = options.method
        if method != 'auto':
            exit('Not Implemented Method: %s' % method)

    try:
        data_path = path.join(path.dirname(path.abspath(__file__)), 'gbk2sjis.dat')
        chardict = read_char_dict(data_path)

        ons = ONSHandler(in_path)
        text = ons.get_script()
        text = hzconvert(text, 'gbk', 'sjis', method, chardict)

        open(out_path, 'wb').write(text)
    except Exception as e:
        if gui:
            from portable import tkMessageBox
            tkMessageBox.showerror(message=repr(e), title='Error!')
            exit()
        raise
    else:
        if gui:
            from portable import tkMessageBox
            tkMessageBox.showinfo(message='转换完成!', title='Finished!')


if __name__ == '__main__':
    main(sys.argv)
