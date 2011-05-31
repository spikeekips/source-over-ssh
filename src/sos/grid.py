# -*- coding: utf-8 -*-

def decorator_keep_settings (func, ) :
    def wrapper (self, *a, **kw) :
        kw.setdefault("settings", dict(), )
        _settings = dict(self.available_settings.items(), )
        _settings.update(kw.get("settings"), )

        kw["settings"] = _settings
        return func(self, *a, **kw)

    return wrapper


class Formatter (object, ) :
    available_settings = dict(
        width=50,
        column_widths=tuple(),
        min_column_width=4,
        padding=0,
        num_columns=1,

        fit_value_width=False,
        with_head=True,
        with_tail=True,
        with_body_line=True,

        body_line_char="-",
        head_line_char="=",
        tail_line_char="=",
        column_sep_in_body_char="|",
        column_sep_in_line_char="+",

        captions=None,
    )

    def __init__ (self, ) :
        pass

    def _get_settings (self, data, settings, ) :
        _settings = dict(self.available_settings.items(), )
        _settings.update(settings, )

        if not _settings.get("column_widths") :
            _settings["column_widths"] = self._calculate_column_width(
                _settings.get("width"),
                _settings.get("num_columns"),
            )

        _settings["column_widths"] = self._check_column_width(
            data,
            settings=_settings,
        )
        if _settings.get("captions") :
            _settings["with_head"] = True

        return _settings

    def format (self, data, **settings) :
        """
        >>> data = (("a", "b", ), )
        >>> check_result_length(Formatter().format(data, num_columns=2, ), )
        True
        >>> check_result_length(Formatter().format(data, num_columns=2, ), )
        True
        >>> _p(Formatter().format(data, num_columns=2, ), )
        +=======================+========================+
        |a                      |b                       |
        +=======================+========================+

        >>> check_result_length(Formatter().format(data, num_columns=2, ), )
        True
        >>> data = (("a" * 10, "b" * 5, ), ("a" * 9, "b" * 4, ), )
        >>> check_result_length(Formatter().format(data, num_columns=2, ), )
        True
        >>> data = (("a", ), )
        >>> check_result_length(Formatter().format(data, num_columns=1, ), )
        True
        >>> _p(Formatter().format(data, num_columns=1, ), )
        +================================================+
        |a                                               |
        +================================================+
        >>> check_result_length(Formatter().format(data, num_columns=1, ))
        True
        >>> list(Formatter().format(data, num_columns=1, ))[1]
        '|a                                               |'

        >>> data = (("a" * 10, "b" * 5, ), ("a" * 3, "b" * 10, ), )
        >>> check_result_length(Formatter().format(data, num_columns=2, ))
        True
        >>> check_result_length(Formatter().format(data, num_columns=2, ))
        True
        >>> check_result_length(Formatter().format(data, column_widths=(30, 10, ), num_columns=3, ))
        True

        >>> data = (("a" * 20, "b" * 5, ), ("a" * 9, "b" * 40, ), )
        >>> check_result_length(Formatter().format(data, column_widths=(10, 20, ), num_columns=3, ))
        True
        >>> print "\\n".join(Formatter().format(data, column_widths=(10, 20, ), num_columns=3, ))
        +==========+====================+================+
        |aaaaaaaaaa|bbbbb               |                |
        |aaaaaaaaaa|                    |                |
        +----------+--------------------+----------------+
        |aaaaaaaaa |bbbbbbbbbbbbbbbbbbbb|                |
        |          |bbbbbbbbbbbbbbbbbbbb|                |
        +==========+====================+================+

        >>> data = (("a" * 20, "b" * 20, ), )
        >>> print "\\n".join(Formatter().format(data, column_widths=(5, 9, ), num_columns=3, ))
        +=====+=========+================================+
        |aaaaa|bbbbbbbbb|                                |
        |aaaaa|bbbbbbbbb|                                |
        |aaaaa|bb       |                                |
        |aaaaa|         |                                |
        +=====+=========+================================+

        >>> data = (("a" * 20, "b" * 20, ), ("a" * 2, "b" * 40, ), )
        >>> _p(Formatter().format(data, column_widths=(5, 9, ), num_columns=3, ))
        +=====+=========+================================+
        |aaaaa|bbbbbbbbb|                                |
        |aaaaa|bbbbbbbbb|                                |
        |aaaaa|bb       |                                |
        |aaaaa|         |                                |
        +-----+---------+--------------------------------+
        |aa   |bbbbbbbbb|                                |
        |     |bbbbbbbbb|                                |
        |     |bbbbbbbbb|                                |
        |     |bbbbbbbbb|                                |
        |     |bbbb     |                                |
        +=====+=========+================================+

        >>> data = (("a", "b", ), ("a", "b", ), )
        >>> _p(Formatter().format(data, num_columns=2, head_line_char="*", tail_line_char="@", ))
        +***********************+************************+
        |a                      |b                       |
        +-----------------------+------------------------+
        |a                      |b                       |
        +@@@@@@@@@@@@@@@@@@@@@@@+@@@@@@@@@@@@@@@@@@@@@@@@+

        >>> _p(Formatter().format(data, num_columns=2, with_head=False, with_tail=False, ))
        |a                      |b                       |
        +-----------------------+------------------------+
        |a                      |b                       |
        >>> _p(Formatter().format(data, num_columns=2, with_head=False, with_tail=False, with_body_line=False, ))
        |a                      |b                       |
        |a                      |b                       |
        >>> _p(Formatter().format(data, padding=1, num_columns=2, with_head=False, with_tail=False, with_body_line=False, ))
        | a                     | b                      |
        | a                     | b                      |

        >>> data = (("a" * 40, "b" * 20, ), )
        >>> check_result_length(Formatter().format(data, padding=1, num_columns=2, ))
        True
        >>> check_result_length(Formatter().format(data, padding=1, num_columns=2, ))
        True
        >>> _p(Formatter().format(data, padding=1, num_columns=2, ))
        +=======================+========================+
        | aaaaaaaaaaaaaaaaaaaaa | bbbbbbbbbbbbbbbbbbbb   |
        | aaaaaaaaaaaaaaaaaaa   |                        |
        +=======================+========================+

        add caption
        >>> data = (("a" * 40, "b" * 20, ), ("a" * 10, "b" * 40, ), )
        >>> check_result_length(Formatter().format(data, num_columns=2, captions=("this is long long long long long long long long long long long key", "this is value", ), ))
        True
        >>> _p(Formatter().format(data, num_columns=2, captions=("this is long long long long long long long long long long long key", "this is value", ), ))
        +=======================+========================+
        |this is long long long |this is value           |
        |long long long long lon|                        |
        |g long long long key   |                        |
        +=======================+========================+
        |aaaaaaaaaaaaaaaaaaaaaaa|bbbbbbbbbbbbbbbbbbbb    |
        |aaaaaaaaaaaaaaaaa      |                        |
        +-----------------------+------------------------+
        |aaaaaaaaaa             |bbbbbbbbbbbbbbbbbbbbbbbb|
        |                       |bbbbbbbbbbbbbbbb        |
        +=======================+========================+

        >>> data = (("a" * 3, "b", ), ("a", "b", ), )
        >>> _p(Formatter().format(data, num_columns=2, padding=1, fit_value_width=True, ))
        +=====+==========================================+
        | aaa | b                                        |
        +-----+------------------------------------------+
        | a   | b                                        |
        +=====+==========================================+

        >>> data = (('/tmp/git.git', '/git'), ('/tmp/test_repo', '/svn (show me the truth)'), )
        >>> _p(Formatter().format(data, column_widths=(15, ), num_columns=2, padding=1, width=50, ))
        +===============+================================+
        | /tmp/git.git  | /git                           |
        +---------------+--------------------------------+
        | /tmp/test_rep | /svn (show me the truth)       |
        | o             |                                |
        +===============+================================+
        >>> _p(Formatter().format(data, min_column_width=15, num_columns=2, padding=1, width=50, ))
        +=======================+========================+
        | /tmp/git.git          | /git                   |
        +-----------------------+------------------------+
        | /tmp/test_repo        | /svn (show me the trut |
        |                       | h)                     |
        +=======================+========================+

        >>> _p(Formatter().format(data, num_columns=2, padding=1, width=100, ))
        +================================================+=================================================+
        | /tmp/git.git                                   | /git                                            |
        +------------------------------------------------+-------------------------------------------------+
        | /tmp/test_repo                                 | /svn (show me the truth)                        |
        +================================================+=================================================+



        """
        _settings = self._get_settings(data, settings, )

        _b = "%s%%%%-%%ds" % _settings.get("column_sep_in_body_char")
        _tmpl_body = (_b * _settings.get("num_columns", )).strip() % tuple(_settings.get("column_widths"))
        _tmpl_body += _settings.get("column_sep_in_body_char")

        _b = "%s%%%%-%%ds" % _settings.get("head_line_char")
        _tmpl_line_head = (_b * _settings.get("num_columns", )).strip() % tuple(_settings.get("column_widths"))
        _tmpl_line_head += _settings.get("head_line_char")

        _b = "%s%%%%-%%ds" % _settings.get("tail_line_char")
        _tmpl_line_tail = (_b * _settings.get("num_columns", )).strip() % tuple(_settings.get("column_widths"))
        _tmpl_line_tail += _settings.get("tail_line_char")

        _b = "%s%%%%-%%ds" % _settings.get("column_sep_in_line_char")
        _tmpl_line = (_b * _settings.get("num_columns", )).strip() % tuple(_settings.get("column_widths"))
        _tmpl_line += _settings.get("column_sep_in_line_char")

        if _settings.get("with_head") :
            yield self.print_line(
                _tmpl_line_head,
                char=_settings.get("head_line_char"),
                sep=_settings.get("head_line_char"),
                settings=_settings,
            )

        if settings.get("captions") :
            for i in self.print_value(_tmpl_body, settings.get("captions"), settings=_settings, ) :
                yield i

            if _settings.get("with_body_line") :
                yield self.print_line(
                    _tmpl_line,
                    char=_settings.get("head_line_char"),
                    sep=_settings.get("column_sep_in_line_char"),
                    settings=_settings,
                )

        _n = 0
        for i in data :
            for j in self.print_value(_tmpl_body, i, settings=_settings, ) :
                yield j

            if _settings.get("with_body_line") and _n != len(data) - 1 :
                yield self.print_line(
                    _tmpl_line,
                    char=_settings.get("body_line_char"),
                    sep=_settings.get("column_sep_in_line_char"),
                    settings=_settings,
                )

            _n += 1

        if _settings.get("with_tail") :
            yield self.print_line(
                _tmpl_line_tail,
                sep=_settings.get("tail_line_char"),
                char=_settings.get("tail_line_char"),
                settings=_settings,
            )

    def _get_max (self, data, column, ) :
        return max(map(lambda x : len(x[column], ), data), )

    def _calculate_column_width (self, width, num_columns=1, ) :
        _cw = (width - num_columns - 1)
        _l = _cw / num_columns
        _n = [_l, ] * (num_columns - 1)
        _o = map(lambda x : x, _n) + [_cw - sum(_n)]
        return tuple(_o)

    @decorator_keep_settings
    def _check_column_width (self, data, settings=None, ) :
        _column_width = list(settings.get("column_widths"))
        if len(_column_width) < settings.get("num_columns") :
            _column_width.extend([0, ] * (settings.get("num_columns") - len(_column_width, )))
            
        _column_width = map(
            lambda x : x < settings.get("min_column_width") and settings.get("min_column_width") or x,
            _column_width
        )

        _current_width = sum(_column_width) + settings.get("num_columns") + 1
        if _current_width > settings.get("width") :
            return self._calculate_column_width(
                settings.get("width"),
                settings.get("num_columns"),
            )
        elif _current_width < settings.get("width") :
            _column_width[-1] = settings.get("width") - sum(
                _column_width[:len(_column_width) - 1]) - settings.get("num_columns") - 1

        if settings.get("fit_value_width") and data :
            for i in range(settings.get("num_columns") - 1, ) :
                _column_width[i] = self._get_max(data, i, ) + (2 * settings.get("padding"))

            _column_width[-1] = settings.get("width") - sum(
                _column_width[:len(_column_width) - 1]) - settings.get("num_columns") - 1

        return tuple(_column_width)

    @decorator_keep_settings
    def print_line (self, tmpl, char="-", sep=" ", settings=None, ) :
        return tmpl % tuple(
            map(
                lambda x : char * settings.get("column_widths")[x],
                range(settings.get("num_columns")),
            ),
        )

    @decorator_keep_settings
    def print_value (self, tmpl, data, settings=None, ) :
        if len(data) < settings.get("num_columns") :
            data = list(data)
            data.extend(["", ] * (settings.get("num_columns") - len(data, )))
            data = tuple(data, )
        elif len(data) > settings.get("num_columns") :
            data = list(data)[:settings.get("num_columns")]

        # cut the each value by whether overflow or not. 
        _column_width = settings.get("column_widths")
        _lines = list()
        for i in range(len(data)) :
            _lines.append(list(), )
            if len(data[i]) <= _column_width[i] - (2 * settings.get("padding")) :
                _lines[i].append(data[i], )
                continue

            _x = range(0, len(data[i]), _column_width[i] - (2 * settings.get("padding")), )
            for j in range(len(_x)) :
                _sl = slice(
                    _x[j],
                    j + 1 < len(_x) and _x[j + 1] or None,
                )
                _lines[i].append(
                    data[i][_sl.start:_sl.stop:_sl.step]
                )

        _b = "%s%%s%s" % (" " * settings.get("padding"), " " * settings.get("padding"), )

        for i in range(max(map(len, _lines, ))) :
            yield tmpl % tuple(i < len(j) and (_b % j[i]) or str() for j in _lines)



if __name__ == "__main__"  :
    def check_result_length (result, ) :
       return list(set(map(len, result))) == [Formatter.available_settings.get("width"), ]
    def _p (result, ) :
       print "\n".join(result, )

    import doctest
    doctest.testmod()



