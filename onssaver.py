#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Skydark Chen'
__version__ = '0.03.dev'
__license__ = 'GPLv2'

import os
import sys


from ons import ONScripterError
from ons.handler import ONSHandler, ONSHandlerError
from ons.saver import ONSSaver, ONSSaverError


class ONSDiffSaver(ONSSaver):
    ONS_NEST_SEARCH_AREA_LIMIT = 50

    def __init__(self, handler, newhandler):
        self.savehandler = newhandler
        super(ONSDiffSaver, self).__init__(handler)

    def save(self):
        handler = self.handler
        savehandler = self.savehandler
        if savehandler.global_variable_border != \
                handler.global_variable_border:
            raise ONSSaverError(
                    'New script has a different global variable border!')

        stack_offset_begin = self.stack_offset
        stack_offset_end = stack_offset_begin + self.num_nest * 4
        current_offset_end = self.current_offset[0]
        current_offset_begin = current_offset_end - 8
        code = self.code

        plain_nest_info = b''
        for type_, addr in self._match_nest_info():
            if type_ == 'label':
                plain_nest_info += self.writeInt(addr)
                #try:
                #    print(addr, savehandler.buf[addr:addr+20].decode('gbk'))
                #except UnicodeDecodeError:
                #    print(addr)
            else:
                plain_nest_info += b''.join(self.writeInt(i) for i in type_[1])
                plain_nest_info += self.writeInt(-addr)

        current_offset = self._match_current_offset()

        ret = b''.join([
            code[:stack_offset_begin],
            plain_nest_info,
            code[stack_offset_end:current_offset_begin],
            current_offset,
            code[current_offset_end:],
            ])
        return ret

    def _match_current_offset(self):
        handler = self.savehandler
        p, current_inline_offset = self.current_offset[:2]
        address = self._match_offset(*self.current_offset[2:])
        current_lno = handler.getLineByAddress(address, relative=False)
        return self.writeInt(current_lno) + \
                self.writeInt(current_inline_offset)

    def _match_nest_info(self):
        new_nest_info = [0] * len(self.nest_info)
        for j, nest_info in enumerate(self.nest_info):
            type_ = nest_info[0]
            new_nest_info[j] = (type_, self._match_offset(*nest_info[1:]))
        return new_nest_info

    def _match_offset(self, addr, label, line, line_offset, line_start_addr):
        # <TODO: match with difflib
        savehandler = self.savehandler
        line_content = self.handler.getLineStringByAddress(line_start_addr)
        try:
            new_label = savehandler.findLabel(label.name)[1]
        except ONSHandlerError:
            # Label not found, can't match
            raise ONSSaverError('Label not found: %s' % str(addr))
        # Label found, try to match with the same line offset

        def try_this_line(newline):
            new_addr = savehandler.getAddressByLine(newline)
            if savehandler.getLineStringByAddress(new_addr) == line_content:
                # matched!
                return new_addr + addr - line_start_addr
            return None

        c = 0
        new_line = new_label.start_line + line_offset
        ret = try_this_line(new_line)
        if ret is not None:
            return ret
        while c < self.ONS_NEST_SEARCH_AREA_LIMIT:
            c += 1
            ret = try_this_line(new_line + c)
            if ret is not None:
                return ret
            ret = try_this_line(new_line - c)
            if ret is not None:
                return ret
        # no match found
        raise ONSSaverError('Label not found: %s' % str(addr))


def help():
    print('Usage: %s old_script_dir new_script_dir [save_files]' % sys.argv[0])
    print('       (save_files default to all save files in old_script_dir)')


def main(argv):
    if len(argv) < 3:
        help()
        sys.exit()
    # oldsave, newsave, olddir, newdir = sys.argv[1:5]
    load_dir, save_dir = argv[1:3]
    save_files = argv[3:]
    if not save_files:
        import glob
        save_files = glob.glob(os.path.join(load_dir, 'save*.dat'))

    try:
        loadhandler = ONSHandler(load_dir)
        savehandler = ONSHandler(save_dir)
    except ONSHandlerError as e:
        print('Error! Can not load scripts!')
        print(e)
        return False

    saver = ONSDiffSaver(loadhandler, savehandler)

    for save_file in save_files:
        print('Processing %s...' % save_file)
        try:
            savedata = open(save_file, 'rb').read()
        except IOError as e:
            print('Error!')
            print('Can not read %s!' % save_file)
            print(e)
            continue

        try:
            saver.load(savedata)
        except ONScripterError as e:
            print('Can not load %s!' % save_file)
            print(e)
            continue
        except AssertionError as e:
            print('Error!')
            print('Not an onscripter save file? %s' % save_file)
            print(e)
            continue

        try:
            new_savedata = saver.save()
        except ONScripterError as e:
            print('Error!')
            print('Can not save %s!' % save_file)
            print(e)
            continue

        new_save_file = os.path.join(save_dir, os.path.split(save_file)[1])
        try:
            open(new_save_file, 'wb').write(new_savedata)
        except IOError as e:
            print('Error!')
            print('Can not write %s!' % save_file)
            print(e)
            continue

        print('Done.')
    print('OK!')


if __name__ == '__main__':
    main(sys.argv)
