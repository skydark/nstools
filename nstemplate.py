#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Usage: nstemplate.py [options] input_file output_file

Options:
  -h --help                show this help
  -b --base BASE_NUM       set base number [default: 1000]
  -e --encoding ENCODING   set input file encoding [default: auto]

"""

# <TODO>(DROPPED!)
# 1. macro
# 2. import with param
# 3. kr_reader_macro
# 4. (NS) kr_reader
# 5. (NS) function rec call
# 6. (NS) setwindow
# 7. (NS) reflect lsp/csp/...
# 8. (NS) mathlib
# 10. (NS) OO
# 13. (NS) text_utils(to_wide, int_to_chinese)
# 14. (NS) queue
# 15. (NS) button interface
# 16. (NS) name/face

import os
import sys
import re
from codecs import open

import chardet
from docopt import docopt

from utils import Struct


DEFAULT_ENCODING = 'utf-8'

py = sys.version_info
py3k = py >= (3, 0, 0)

if py3k:
    to_unicode = lambda s, encoding=DEFAULT_ENCODING:\
            s.decode(encoding) if isinstance(s, bytes) else str(s)
    isstr = lambda s: isinstance(s, str)
    encode = lambda s, encoding: bytes(s, encoding)
else:
    to_unicode = lambda s, encoding=DEFAULT_ENCODING:\
            s if isinstance(s, unicode) else s.decode(encoding)
    isstr = lambda s: isinstance(s, basestring)
    encode = lambda s, encoding: s.encode(encoding)


def debug(s):
    print('DEBUG: ' + str(s))


class NSTParser(object):
    _re_exps = {
            'comment': r'^(\s*)@##(.*)$',
            'raw': r'^(\s*)@#(|[^#].*)$',
            'var': r'(%|\$)(\d+)',
            'format': r'@\{([^}]+)\}',
            'def': r'^(\s*)(@def)(\s+)(\w+)(\s*)(.*)',
            'python': r'^(\s*)@python.*$',
            'in_python': r'^(\s*)@(.*)$',
            'import': r'^\s*@import\s+(?P<filename>[^\s]+)' + \
                    r'(\s+as\s+(?P<name>[^\s]+))?\s*$',
            }
    _resubs = {
            'raw': r'\1\2',
            'in_python': r'\2',
            'def_make': r'\tdefsub \4',
            }

    def __init__(self, **options):
        self.locals = {
                '__base': 1000,
                '__max_var': 0,
                '__encoding': 'auto',
                '__': lambda s: self.outlines.append(
                    to_unicode(s.format(**self.locals))),
                '__s': lambda s: map(str.strip, s.split(',')),
                }
        if '__' in options:  # can not bind '__': `self`
            del options['__']
        self.locals.update(options)

        self.lines = []
        self.outlines = []
        self.defsubs = []
        self.python_lines = []

        for name, re_exp in self._re_exps.items():
            setattr(self, '_re_' + name, re.compile(re_exp))

        self.state = 'default'
        self._parse = dict((state, getattr(self, '_parse_' + state))
                for state in ('python', 'default'))

    def get_name_by_filename(self, filename):
        name = os.path.splitext(os.path.basename(filename))[0]
        return name

    def read_lines(self, filename, encoding=None):
        if encoding is None or encoding == 'auto':
            source = open(filename, 'rb').read()
            encoding = chardet.detect(source)['encoding']
            debug('Guess encoding for %s: %s' % (filename, encoding))
        source = open(filename, 'rb', encoding=encoding).read()
        lines = source.splitlines()
        return lines

    def _pre_parse(self, line, lno):
        def rebase(m):
            groups = m.groups()
            var = int(groups[-1])
            self.locals['__max_var'] = max(var, self.locals['__max_var'])
            return ''.join(groups[:-1]) + str(self.locals['__base'] + var)

        if self._re_comment.match(line):
            return None

        if self._re_raw.match(line):
            self.outlines.append(self._re_raw.sub(self._resubs['raw'], line))
            return None

        line = '"'.join(self._re_var.sub(rebase, part) if i % 2 == 0 else part
                for i, part in enumerate(line.split('"')))
        return line

    def _parse_default(self, line, lno):
        if self._re_python.match(line):
            self.state = 'python'
            return

        format = lambda m: str(eval(m.groups()[0], self.locals))
        line = '"'.join(self._re_format.sub(format, part)
                if i % 2 == 0 else part
                for i, part in enumerate(line.split('"')))

        if self._re_def.match(line):
            def re_def_sub(m):
                groups = m.groups()
                p = groups[0] + '\tget_param ' + groups[5] if groups[5] else ''
                return  '{0}*{3}\r\n{p}'.format(*groups, p=p)

            re_def = self._re_def
            self.defsubs.append(re_def.sub(self._resubs['def_make'], line))
            line = re_def.sub(re_def_sub, line)
            self.outlines.append(line)
            return

        m = self._re_import.match(line)
        if m:
            d = m.groupdict()
            filename = d['filename']
            name = d['name'] or self.get_name_by_filename(filename)
            importer = self.__class__(**self.locals)
            lines = importer.read_lines(filename)
            importer.parse(name, lines)
            self.outlines.extend(importer.outlines)
            if name:
                self.locals[name] = Struct(**importer.locals)
            return

        self.outlines.append(line)

    def _parse_python(self, line, lno):
        if self._re_in_python.match(line):
            line = self._re_in_python.sub(self._resubs['in_python'], line)
            self.python_lines.append(line)
        else:
            exec('\n'.join(self.python_lines), self.locals)
            self.python_lines = []
            self.state = 'default'
            return True

    def parse(self, name, lines=None):
        if lines is None:
            lines = name
            name = self.get_name_by_filename(name)
        if isstr(lines):
            lines = self.read_lines(lines, encoding=self.locals['__encoding'])
        self.locals['__current_name'] = to_unicode(name)
        self.lines = lines
        # debug((name, self.locals['__encoding']))

        for lno, line in enumerate(lines):
            try:
                line = self._pre_parse(line, lno)
                if line is not None:
                    while self._parse[self.state](line, lno):
                        pass
            except:
                print('Error when parsing %s at line %s: %s'\
                        % (name, lno + 1, line))
                raise

        self.make_info_lines()
        self.locals['__current_name'] = ''

    def make_info_lines(self):
        outlines = self.outlines
        outlines.append('\r\n*__nst_defsub_%s' % self.locals['__current_name'])
        outlines.extend(self.defsubs)
        outlines.append('\treturn\r\n')
        outlines.append('mov %%__nst_base, %s\r\n\r\n'
                % (self.locals['__base'] + self.locals['__max_var'] + 1))

    def write(self, output):
        if isstr(output):
            output = open(output, 'wb', encoding='GBK')
        output.write('\r\n'.join(self.outlines))


def help():
    exit(__doc__.strip())


def main(args):
    options, arguments = docopt(__doc__)
    if not(str(options.base).isdigit() and len(arguments) == 2):
        help()
    encoding = options.encoding
    src_name = arguments[0]
    dst_name = arguments[1]

    parser = NSTParser(__encoding=encoding, __base=int(options.base))
    parser.parse(src_name)
    parser.write(dst_name)


if __name__ == '__main__':
    main(sys.argv)
