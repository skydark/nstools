# -*- coding: utf-8 -*-

import os


def cd_once(directory, func, *args, **kwargs):
    curpath = os.path.abspath('.')
    os.chdir(directory)
    ret = func(*args, **kwargs)
    os.chdir(curpath)
    return ret


class Struct(object):
    def __init__(self, str=None, **entries):
        if str and entries == {}:
            self.from_str(str)
        else:
            if str is not None:
                entries['str'] = str
            self.__dict__.update(entries)

    def to_str(self, format='json'):
        d = dict((key, value) for key, value in self.__dict__.items()
                if not key.startswith('_'))
        return json.dumps(d)

    def from_str(self, s, format='json'):
        d = json.loads(s)
        self.__dict__.update(d)
        return self
