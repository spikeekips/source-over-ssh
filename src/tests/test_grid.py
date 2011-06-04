# -*- coding: utf-8 -*-




"""

>>> data = (("a", "b", ), )
>>> check_result_length(Formatter().format(data, num_columns=2, ), )
True
>>> check_result_length(Formatter().format(data, num_columns=2, ), )
True
>>> _p(Formatter().format(data, num_columns=2, ), )
==================================================
|a                      |b                       |
==================================================

>>> check_result_length(Formatter().format(data, num_columns=2, ), )
True
>>> data = (("a" * 10, "b" * 5, ), ("a" * 9, "b" * 4, ), )
>>> check_result_length(Formatter().format(data, num_columns=2, ), )
True
>>> data = (("a", ), )
>>> check_result_length(Formatter().format(data, num_columns=1, ), )
True
>>> _p(Formatter().format(data, num_columns=1, ), )
==================================================
|a                                               |
==================================================
>>> check_result_length(Formatter().format(data, num_columns=1, ))
True
>>> list(Formatter().format(data, num_columns=1, ))[1]
'|a                                               |'

>>> data = (("a" * 10, "b" * 5, ), ("a" * 3, "b" * 10, ), )
>>> check_result_length(Formatter().format(data, num_columns=2, ))
True
>>> check_result_length(Formatter().format(data, num_columns=2, ))
True
>>> check_result_length(Formatter().format(
...    data, column_widths=(30, 10, ), num_columns=3, ))
True

>>> data = (("a" * 20, "b" * 5, ), ("a" * 9, "b" * 40, ), )
>>> check_result_length(Formatter().format(data, column_widths=(10, 20, ), num_columns=3, ))
True
>>> print "\\n".join(Formatter().format(data, column_widths=(10, 20, ), num_columns=3, ))
==================================================
|aaaaaaaaaa|bbbbb               |                |
|aaaaaaaaaa|                    |                |
+----------+--------------------+----------------+
|aaaaaaaaa |bbbbbbbbbbbbbbbbbbbb|                |
|          |bbbbbbbbbbbbbbbbbbbb|                |
==================================================

>>> data = (("a" * 20, "b" * 20, ), )
>>> print "\\n".join(Formatter().format(data, column_widths=(5, 9, ), num_columns=3, ))
==================================================
|aaaaa|bbbbbbbbb|                                |
|aaaaa|bbbbbbbbb|                                |
|aaaaa|bb       |                                |
|aaaaa|         |                                |
==================================================

>>> data = (("a" * 20, "b" * 20, ), ("a" * 2, "b" * 40, ), )
>>> _p(Formatter().format(data, column_widths=(5, 9, ), num_columns=3, ))
==================================================
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
==================================================

>>> data = (("a", "b", ), ("a", "b", ), )
>>> _p(Formatter().format(data, num_columns=2, head_line_char="*", tail_line_char="@", ))
**************************************************
|a                      |b                       |
+-----------------------+------------------------+
|a                      |b                       |
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

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
==================================================
| aaaaaaaaaaaaaaaaaaaaa | bbbbbbbbbbbbbbbbbbbb   |
| aaaaaaaaaaaaaaaaaaa   |                        |
==================================================

add caption
>>> data = (("a" * 40, "b" * 20, ), ("a" * 10, "b" * 40, ), )
>>> check_result_length(Formatter().format(data, num_columns=2, captions=("this is long long long long long long long long long long long key", "this is value", ), ))
True
>>> _p(Formatter().format(data, num_columns=2, captions=("this is long long long long long long long long long long long key", "this is value", ), ))
==================================================
|this is long long long |this is value           |
|long long long long lon|                        |
|g long long long key   |                        |
+=======================+========================+
|aaaaaaaaaaaaaaaaaaaaaaa|bbbbbbbbbbbbbbbbbbbb    |
|aaaaaaaaaaaaaaaaa      |                        |
+-----------------------+------------------------+
|aaaaaaaaaa             |bbbbbbbbbbbbbbbbbbbbbbbb|
|                       |bbbbbbbbbbbbbbbb        |
==================================================

>>> data = (("a" * 3, "b", ), ("a", "b", ), )
>>> _p(Formatter().format(data, num_columns=2, padding=1, fit_value_width=True, ))
==================================================
| aaa | b                                        |
+-----+------------------------------------------+
| a   | b                                        |
==================================================

>>> data = (('/tmp/git.git', '/git'), ('/tmp/test_repo', '/svn (show me the truth)'), )
>>> _p(Formatter().format(data, column_widths=(15, ), num_columns=2, padding=1, width=50, ))
==================================================
| /tmp/git.git  | /git                           |
+---------------+--------------------------------+
| /tmp/test_rep | /svn (show me the truth)       |
| o             |                                |
==================================================
>>> _p(Formatter().format(data, min_column_width=15, num_columns=2, padding=1, width=50, ))
==================================================
| /tmp/git.git          | /git                   |
+-----------------------+------------------------+
| /tmp/test_repo        | /svn (show me the trut |
|                       | h)                     |
==================================================

>>> _p(Formatter().format(data, num_columns=2, padding=1, width=100, ))
====================================================================================================
| /tmp/git.git                                   | /git                                            |
+------------------------------------------------+-------------------------------------------------+
| /tmp/test_repo                                 | /svn (show me the truth)                        |
====================================================================================================



"""

if __name__ == "__main__" :
    from sos.grid import Formatter 

    def check_result_length (result, ) :
       return list(set(map(len, result))) == [Formatter.available_settings.get("width"), ]
    def _p (result, ) :
       print "\n".join(result, )

    import doctest
    doctest.testmod()

