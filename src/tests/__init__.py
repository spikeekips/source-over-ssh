# -*- coding: utf-8 -*-

__all__ = [
    "test_config_db",
    "test_grid",
    "test_shell",
    "test_svn",
]


if __name__ == "__main__" :
    import doctest
    for i in __all__ :
        print ("%%-%ds: %%s" % (max(map(len, __all__)) + 1)) % (
            i,
            doctest.testmod(__import__(i, None, None, [i, ], ), ),
        )



