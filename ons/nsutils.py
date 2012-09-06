# -*- coding: utf-8 -*-


from portable import chr, to_unicode, UEMPTY, py3k

_fullwide_map = [chr(65248 + i) for i in range(128)]
_fullwide_map[32] = to_unicode('　')
_fullwide_map = UEMPTY.join(_fullwide_map)


def get_widechar_converter(excepts=None):
    '''
    >>> f = get_widechar_converter(r'/\@')
    >>> s = 'wc是@厕所的意思.../'
    >>> print(f(s) if py3k else f(s.decode('utf-8')).encode('utf-8'))
    ｗｃ是@厕所的意思．．．/
    '''
    if excepts:
        fm = list(_fullwide_map)
        for char in excepts:
            fm[ord(char)] = char
        fm = UEMPTY.join(fm)
    else:
        fm = _fullwide_map
    return lambda s: s.translate(fm)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
