# -*- coding: utf-8 -*-

"""

>>> from sos.servers import SVNCommandParser

with `edit-pipeline`
>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev/a/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ) and None

with spacless `edit-pipeline`
>>> a = "(2(edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops )47:svn+ssh://srothan@dev/a/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) )"
>>> SVNCommandParser(a, ) and None

>>> a = "( success ( ) ) ( success ( 36:cb32cf5e-01a4-4eae-a809-c6ba03748993 35:svn+ssh://srothan@dev/b ( mergeinfo ) ) ) "
>>> SVNCommandParser(a, ) and None

with bad command
>>> a = "( success ( 2 2 ( ) ( edit-pipeline svndiff1 absent-entries commit-revprops depth log-revprops partial-replay ) ) ) "
>>> SVNCommandParser(a, ) and None
Traceback (most recent call last):
...
BAD_SVN_REPOSITORY_COMMAND: bad svn repository command

>>> a = "( success ( ( ANONYMOUS EXTERNAL ) 36:cb32cf5e-01a4-4eae-a809-c6ba03748993 ) ) "
>>> SVNCommandParser(a, ) and None
Traceback (most recent call last):
...
BAD_SVN_REPOSITORY_COMMAND: bad svn repository command
>>> a = "( EXTERNAL ( 0: ) ) "
>>> SVNCommandParser(a, ) and None
Traceback (most recent call last):
...
BAD_SVN_REPOSITORY_COMMAND: bad svn repository command
>>> a = "( commit ( 21:09348102938401284029\\n ( ) false ( ( 7:svn:log 21:09348102938401284029\\n ) ) ) ) "
>>> SVNCommandParser(a, ) and None
Traceback (most recent call last):
...
BAD_SVN_REPOSITORY_COMMAND: bad svn repository command
>>> a = "( success ( ( ) 0: ) ) ( success ( ) ) "
>>> SVNCommandParser(a, ) and None
Traceback (most recent call last):
...
BAD_SVN_REPOSITORY_COMMAND: bad svn repository command
>>> a = "( success ( ) ) ( success ( ( ) 0: ) ) ( 12 ( 27:2011-05-25T06:30:11.163634Z ) ( 7:srothan ) ( ) ) "
>>> SVNCommandParser(a, ) and None
Traceback (most recent call last):
...
BAD_SVN_REPOSITORY_COMMAND: bad svn repository command

with normal `edit-pipeline`
>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev/a/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ).replace_path("a", "bc")
'( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 48:svn+ssh://srothan@dev/bc/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) '
>>> SVNCommandParser(a, ).replace_path("/a", "/bc")
'( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 48:svn+ssh://srothan@dev/bc/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) '

with abnormal path
>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev///a/////////dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ).replace_path("//a///", "/bc///")
'( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 48:svn+ssh://srothan@dev/bc/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) '

>>> a = "( success ( ) ) ( success ( 36:cb32cf5e-01a4-4eae-a809-c6ba03748993 27:svn+ssh://srothan@dev/a/dir ( mergeinfo ) ) ) "
>>> SVNCommandParser(a, ).replace_path("a", "cd", )
'( success ( ) ) ( success ( 36:cb32cf5e-01a4-4eae-a809-c6ba03748993 28:svn+ssh://srothan@dev/cd/dir ( mergeinfo ) ) ) '

>>> a = "( failure ( ( 210005 68:No repository found in 'svn+ssh://srothan@dev/a/dlfjalsd' 63:/build/buildd/subversion-1.6.12dfsg/subversion/svnserve/serve.c 2847 ) ) ) "
>>> SVNCommandParser(a, ).replace_path("a", "cd", )
"( failure ( ( 210005 68:No repository found in 'svn+ssh://srothan@dev/cd/dlfjalsd' 63:/build/buildd/subversion-1.6.12dfsg/subversion/svnserve/serve.c 2847 ) ) ) "

>>> a = '( reparent ( 23:svn+ssh://srothan@dev/a ) ) '
>>> SVNCommandParser(a, ).replace_path("a", "cd", )
'( reparent ( 24:svn+ssh://srothan@dev/cd ) ) '

>>> a = '( open-root ( ( ) 2:d0 ) ) ( delete-entry ( 13:.bash_history ( 1 ) 2:d0 ) ) ( delete-entry ( 7:.bashrc ( 1 ) 2:d0 ) ) ( open-dir ( 5:trunk 2:d0 2:d1 ( ) ) ) ( add-file ( 19:trunk/.bash_history 2:d1 2:c2 ( 40:svn+ssh://spikeekips@dev/a/.bash_history 1 ) ) ) ( close-file ( 2:c2 ( ) ) ) ( add-file ( 13:trunk/.bashrc 2:d1 2:c3 ( 34:svn+ssh://spikeekips@dev/a/.bashrc 1 ) ) ) ( close-file ( 2:c3 ( ) ) ) ( close-dir ( 2:d1 ) ) ( close-dir ( 2:d0 ) ) ( close-edit ( ) ) '
>>> SVNCommandParser(a, ).replace_path("a", "bc")
'( open-root ( ( ) 2:d0 ) ) ( delete-entry ( 13:.bash_history ( 1 ) 2:d0 ) ) ( delete-entry ( 7:.bashrc ( 1 ) 2:d0 ) ) ( open-dir ( 5:trunk 2:d0 2:d1 ( ) ) ) ( add-file ( 19:trunk/.bash_history 2:d1 2:c2 ( 41:svn+ssh://spikeekips@dev/bc/.bash_history 1 ) ) ) ( close-file ( 2:c2 ( ) ) ) ( add-file ( 13:trunk/.bashrc 2:d1 2:c3 ( 35:svn+ssh://spikeekips@dev/bc/.bashrc 1 ) ) ) ( close-file ( 2:c3 ( ) ) ) ( close-dir ( 2:d1 ) ) ( close-dir ( 2:d0 ) ) ( close-edit ( ) ) '

>>> a = '(reparent ( 23:svn+ssh://srothan@dev/a))'
>>> SVNCommandParser(a, ).replace_path("a", "cd", )
'(reparent ( 24:svn+ssh://srothan@dev/cd))'

>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev/a/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ).get_repository_path()
'/a/dir%20with%20whitespace'

>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev/a/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ).is_in(["/a/", "/b/", ])
True

>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev/a 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ).is_in(["/a/", "/b/", ])
True

>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev/a/dir%20with%20whitespace 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ).get_alias(["/a/", "/b/", ])
'/a/'

>>> a = "( 2 ( edit-pipeline svndiff1 absent-entries depth mergeinfo log-revprops ) 47:svn+ssh://srothan@dev/a 21:SVN/1.6.16 (r1073529) ( ) ) "
>>> SVNCommandParser(a, ).get_alias(["a", "b", ])
'a'
"""


if __name__ == "__main__" :
    import doctest
    doctest.testmod()


