# -*- coding: utf-8 -*-

import re, os

RE_PREPATH = re.compile("^[\/]*", )
def normpath (p, ) :
    return RE_PREPATH.sub("/", os.path.normpath(p, ), )

RE_BLANK = re.compile("\s")
def shlex_combine (l, ) :
    """
    >>> shlex_combine(["1", "2 3"])
    '1 "2 3"'
    >>> shlex_combine(["1", "2 3", "4", "5"])
    '1 "2 3" 4 5'
    >>> shlex_combine(["1", "2 3 ", "4", "5"])
    '1 "2 3 " 4 5'

    """
    _s = str()
    for i in l :
        _s += " %s" % str(RE_BLANK.search(i) and ("\"%s\"" % i) or i)

    return _s.strip()

################################################################################
# foramt output
import grid
def format_help (v, width=50, *a, **kw) :
    if width < 50 :
        width = 50

    v = map(lambda x: [x[0], ": " + x[1], ], v)
    return grid.Formatter().format(v,
        width=width,
        num_columns=2,
        padding=0,
        with_body_line=False,
        column_sep_in_line_char=" ",
        column_sep_in_body_char=" ",
        fit_value_width=True,
        with_head=False,
        with_tail=False,
    )

def format_data (v, width=50, *a, **kw) :
    if width < 50 :
        width = 50

    return grid.Formatter().format(v,
        width=width,
        num_columns=2,
        padding=1,
        min_column_width=15,
        fit_value_width=True,
        #with_body_line=False,
        column_sep_in_line_char=" ",
        column_sep_in_body_char=" ",
        #with_head=False,
        #with_tail=False,
    )



if __name__ == "__main__" :
    import doctest
    doctest.testmod()


