# -*- coding: utf-8 -*-

import logging
import os
import re
import urlparse
import urllib

from twisted.python import log


def info (s, ) :
    log.theLogPublisher.msg(s, logLevel=logging.INFO, )


def debug (s, ) :
    log.theLogPublisher.msg(s, logLevel=logging.DEBUG, )


log.msg = lambda *a, **kw : debug(" ".join(a), )


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


def is_remote_repository_path (path, ) :
    return bool(urlparse.urlsplit(path).netloc.strip(), )


def parse_remote_repository (uri, ) :
    _pa = urlparse.urlsplit(uri)
    (_a_user, _a_host, ) = urllib.splituser(_pa.netloc, )
    _user, _password = None, None
    if _a_user :
        (_user, _password, ) = urllib.splitpasswd(_a_user, )
    _defaut_port = _pa.scheme.lower() in ("svn+ssh", "ssh", ) and 22 or None
    (_host, _port, ) = urllib.splitnport(_a_host, defport=_defaut_port, )

    return dict(
        host=_host,
        port=_port,
        scheme=_pa.scheme.lower(),
        user=_user,
        password=_password,
        path=os.path.normpath(
            _pa.path.strip().startswith("/") and _pa.path or ("/" + _pa.path)
        ),
    )


##################################################
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

    _kw = dict(
        width=width,
        num_columns=2,
        padding=1,
        min_column_width=15,
        fit_value_width=True,
        column_sep_in_line_char=" ",
        column_sep_in_body_char=" ",
        #with_body_line=False,
        #with_head=False,
        #with_tail=False,
    )
    _kw.update(kw, )

    return grid.Formatter().format(v, **_kw)


if __name__ == "__main__" :
    import doctest
    doctest.testmod()
