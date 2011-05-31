# -*- coding: utf-8 -*-

class _BaseException (Exception, ) : 
    """
    >>> try :
    ...     raise _BaseException
    ... except Exception, e :
    ...     print e
    <BLANKLINE>

    >>> try :
    ...     raise _BaseException("this is message")
    ... except Exception, e :
    ...     print e
    this is message

    >>> class inherited (_BaseException, ) :
    ...     _message = "show me"
    >>> try :
    ...     raise inherited
    ... except Exception, e :
    ...     print e
    show me
    >>> try :
    ...     raise inherited("this is message")
    ... except Exception, e :
    ...     print e
    this is message
    """

    _message = str()

    def __init__ (self, message=None, *a, **kw) :
        super(BaseException, self).__init__(*a, **kw)
        if message :
            self._message = message

    def _get_message (self, ) : 
        return self._message

    def _set_message (self, s, ) : 
        self._message = s 

    message = property(_get_message, _set_message, )

    def __str__ (self, ) :
        return self.message

class NO_SUCH_COMMAND (_BaseException, ) :
    _message = "no such command"

class NOT_ENOUGH_ARGUMENT (_BaseException, ) :
    _message = "not enough argument"

class BAD_ARGUMENT (_BaseException, ) :
    _message = "bad argument"

class PERMISSION_DENIED (_BaseException, ) :
    _message = "permission denied"

class QUIT (_BaseException, ) : pass

class CLEAR (_BaseException, ) : pass

class BAD_SVN_REPOSITORY_COMMAND (_BaseException ) :
    _message = "bad svn repository command"

if __name__ == "__main__" :
    import doctest
    doctest.testmod()

