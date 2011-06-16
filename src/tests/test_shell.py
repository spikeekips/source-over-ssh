# -*- coding: utf-8 -*-



"""
>>> from sos.shell import BaseCommandParser, CommandParser, AdminCommandParser, ShellCommand
>>> from sos.config_db import ConfigDatabase

>>> PUBLIC_KEY = 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAxbgqxA6IQO8ieZEGQAyZuOCe+ds7LSbjjCnUBzFAyVLJZKlxv+t1JdY+iLi/x/Q3tBHccr7Ueiy+I38AouwOUn81UiViAU6IquNFlOMYMB/IoS5tVYEbHxoYpsZTUi/CuRNOLDfKG0avAXDSdQ9mp2ln1Ovv3pHQLeUuWni5ecslVC36vxpL49eLxr6uXaMnhDyyl9PbMnoudMeiyyyZVNIKK+QEonPLkxgYPk9l1baAtEAph/zDsOwHfwo0DYgt8cPwyO6nzI9BoifVYWavCQoRsGtotf4AktTfL2AArJQc9jLLlzYsPwXK8g2QTLCHm7FED+Wm3T42Tsmn31eYGw== dir@dir.com'
>>> PUBLIC_KEY0 = 'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAxbgqxA6IQO8ieZEGQAyZuOCe+ds7LSbjjCnUBzFAyVLJZKlxv+t1JdY+iLi/x/Q3tBHccr7Ueiy+I38AouwOUn81UiViAU6IquNFlOMYMB/IoS5tVYEbHxoYpsZTUi/CuRNOLDfKG0avAXDSdQ9mp2ln1Ovv3pHQLeUuWni5ecslVC36vxpL49eLxr6uXaMnhDyyl9PbMnoudMeiyyyZVNIKK+QEonPLkxgYPk9l1baAtEAph/zDsOwHfwo0DYgt8cPwyO6nzI9BoifVYWavCQoRsGtotf4AktTfL2AArJQc9jLLlzYsPwXK8g2QTLCHm7FED+Wm3T42Tsmn31eYGw== dir@dir.co.kr'


>>> type(BaseCommandParser("help", ).get_help(("help", ), )) in (list, tuple, )
True
>>> type(BaseCommandParser("help", ).get_help("help", )) in (list, tuple, )
True
>>> BaseCommandParser("help", ).get_help("helippng", )
Traceback (most recent call last):
...
NO_SUCH_COMMAND: no such command

>>> type(BaseCommandParser("help", ).get_help(("help", "a", ), )) in (list, tuple, )
True


>>> CommandParser("help").parse()
{'command': ['help']}
>>> CommandParser("help user").parse()
{'args': ('user',), 'command': ['help']}

>>> CommandParser(None, ).get_help()
(('COMMANDS', "'public_key', 'realname', 'quit', 'clear', 'repo', 'user', 'password', 'email', 'help'"),)
>>> CommandParser(None, ).get_help("password", )
(('password', 'set password. $ password <new password>'),)

>>> CommandParser(None, ).get_help(("public_key", "view", ), )
(('public_key view', 'view public key. $ public_key view'),)
>>> CommandParser(None, ).get_help("public_key view", )
(('public_key view', 'view public key. $ public_key view'),)
>>> CommandParser(None, ).get_help("public_key", )
(('public_key remove', 'remove public key. $ public_key remove'), ('public_key save', 'save public key. $ public_key save <key>'), ('public_key view', 'view public key. $ public_key view'))
>>> CommandParser(None, ).get_help("user", )
(('user remove', 'remove user. $ user remove'), ('user rename', 'rename username. $ user rename <new name>'), ('user view', 'view user information. $ user view'))


>>> CommandParser("password").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument

>>> CommandParser("password findme").parse()
{'args': ('findme',), 'command': ['password']}
>>> CommandParser("password 'other user' findme").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument

>>> CommandParser("user view").parse()
{'command': ('user', 'view')}
>>> CommandParser("user remove").parse()
{'command': ('user', 'remove')}
>>> CommandParser("user rename").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument


>>> CommandParser("user rename 'findme' ").parse()
{'command': ('user', 'rename'), 'args': ('findme',)}


>>> CommandParser("email", ).parse()
{'command': ['email']}
>>> CommandParser("email findme@dir.com", ).parse()
{'args': ('findme@dir.com',), 'command': ['email']}

with bad email address
>>> CommandParser("email @dir.com", ).parse()
Traceback (most recent call last):
...
BAD_ARGUMENT: invalid email address.

>>> CommandParser("realname", ).parse()
{'command': ['realname']}
>>> CommandParser("realname spikeekips", ).parse()
{'args': ('spikeekips',), 'command': ['realname']}


>>> CommandParser("public_key", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("public_key view", ).parse()
{'command': ('public_key', 'view')}
>>> CommandParser("public_key remove", ).parse()
{'command': ('public_key', 'remove')}
>>> CommandParser("public_key save ", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument

>>> CommandParser("public_key save %s" % PUBLIC_KEY0, ).parse() == {'command': ('public_key', 'save'), 'args': (PUBLIC_KEY0,)}
True
>>> CommandParser("repo", ).parse()
{'command': ['repo']}
>>> CommandParser("repo list", ).parse()
{'command': ('repo', 'list')}
>>> CommandParser("repo fin", ).parse()
Traceback (most recent call last):
...
BAD_ARGUMENT: bad argument


>>> _r = CommandParser("admin repo list", ).parse()
>>> _r
{'admin': True, 'command': ('repo', 'list')}
>>> "admin" in _r
True

>>> type(AdminCommandParser(None, ).get_help("admin", )) in (list, tuple, )
True
>>> type(AdminCommandParser(None, ).get_help("admin public_key", )) in (list, tuple, )
True
>>> type(AdminCommandParser(None, ).get_help("admin public_key view", )) in (list, tuple, )
True


>>> CommandParser("admin repo list", ).parse()
{'admin': True, 'command': ('repo', 'list')}
>>> CommandParser("admin repo add \\'spikes root\\' /workspace/spike/", ).parse()
{'admin': True, 'command': ('repo', 'add'), 'args': ('spikes root', '/workspace/spike/')}
>>> CommandParser("admin repo add \\'spikes root\\' ", ).parse()
{'admin': True, 'command': ('repo', 'add'), 'args': ('spikes root',)}

>>> CommandParser("admin repo remove \\'spikes root\\' ", ).parse()
{'admin': True, 'command': ('repo', 'remove'), 'args': ('spikes root',)}
>>> CommandParser("admin repo remove", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin repo rename \\'spikes root\\' \\'new root\\'", ).parse()
{'admin': True, 'command': ('repo', 'rename'), 'args': ('spikes root', 'new root')}
>>> CommandParser("admin repo rename \\'spikes root\\' ", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument

>>> CommandParser("admin repo allow", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin repo allow user spikeekips ", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin repo allow user spikeekips \\'spikes root\\' ", ).parse()
{'username': 'spikeekips', 'admin': True, 'command': ('repo', 'allow', 'user'), 'args': ('spikes root',)}

>>> CommandParser("admin user").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin user list").parse()
{'admin': True, 'command': ('user', 'list')}

>>> CommandParser("admin user search").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin user view").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin user search fidnme").parse()
{'admin': True, 'command': ('user', 'search'), 'args': ('fidnme',)}
>>> CommandParser("admin user view spikeekips").parse()
{'username': 'spikeekips', 'admin': True, 'command': ('user', 'view')}

>>> CommandParser("admin user add spikeekips this-is-password").parse()
{'username': 'spikeekips', 'admin': True, 'command': ('user', 'add'), 'args': ('this-is-password',)}

>>> CommandParser("admin user rename spikeekips \\'new name\\'").parse()
Traceback (most recent call last):
...
BAD_ARGUMENT: invalid username.

>>> CommandParser("admin user rename spikeekips \\'newname\\'").parse()
{'username': 'spikeekips', 'admin': True, 'command': ('user', 'rename'), 'args': ('newname',)}

>>> CommandParser("admin user remove spikeekips").parse()
{'username': 'spikeekips', 'admin': True, 'command': ('user', 'remove')}
>>> CommandParser("admin user remove").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument

>>> CommandParser("admin email", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin email spikeekips", ).parse()
{'username': ('spikeekips',), 'admin': True, 'command': ['email']}
>>> CommandParser("admin email spikeekips findme@dir.com", ).parse()
{'username': 'spikeekips', 'admin': True, 'args': ('findme@dir.com',), 'command': ['email']}

with bad email address
>>> CommandParser("admin email spikeekips @dir.com", ).parse()
Traceback (most recent call last):
...
BAD_ARGUMENT: invalid email address.


>>> CommandParser("admin realname", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin realname spikeekips", ).parse()
{'username': 'spikeekips', 'admin': True, 'command': ['realname']}
>>> CommandParser("admin realname spikeekips findme@dir.com", ).parse()
{'username': 'spikeekips', 'admin': True, 'args': ('findme@dir.com',), 'command': ['realname']}

with bad realname address
>>> CommandParser("admin realname spikeekips @dir.com", ).parse()
{'username': 'spikeekips', 'admin': True, 'args': ('@dir.com',), 'command': ['realname']}


>>> CommandParser("admin public_key", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin public_key view ", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin public_key view spikeekips ", ).parse()
{'username': 'spikeekips', 'admin': True, 'command': ('public_key', 'view')}
>>> CommandParser("admin public_key remove", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin public_key remove spikeekips", ).parse()
{'username': 'spikeekips', 'admin': True, 'command': ('public_key', 'remove')}
>>> CommandParser("admin public_key save ", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin public_key save spikeekips ", ).parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin public_key save spikeekips %s" % PUBLIC_KEY0, ).parse() == {'username': 'spikeekips', 'admin': True, 'command': ('public_key', 'save'), 'args': (PUBLIC_KEY0,)}
True

>>> CommandParser("admin password").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin password findme").parse()
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> CommandParser("admin password 'other user' findme").parse()
{'username': 'other user', 'admin': True, 'args': ('findme',), 'command': ['password']}

>>> _cd = ConfigDatabase.from_string("", )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("clear")
Traceback (most recent call last):
...
CLEAR
>>> _sc.run("clear a b c ")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument


>>> _cd = ConfigDatabase.from_string("", )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("quit")
Traceback (most recent call last):
...
QUIT
>>> _sc.run("quit a b c ")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument


>>> _cd = ConfigDatabase.from_string("", )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("help")
['', 'usage:', "COMMANDS : 'public_key', 'realname', 'quit', 'clear', 'repo', 'user', 'password', 'email', 'help'  ", '']

>>> _sc.run("help quit a b c")
['', 'usage:', 'quit : quit $ quit                                                                                 ', '']
>>> _sc.run("help quit")
['', 'usage:', 'quit : quit $ quit                                                                                 ', '']
>>> _sc.run("help admin") is not None
True
>>> _sc.run("help admin user view")
['', 'usage:', 'admin user view : $ admin user view <username>                                                     ', '']

>>> _cfg = "[user:dir]\\nadmin=on\\npassword = thisispassword\\nrealname = Spike-dir\\nemail = dir@dir.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, window_size=(40, 50, ))
>>> print "\\n".join(_sc.run("user view"), )
==================================================
 key             value                           
=============== ================================ 
 username        dir                             
--------------- -------------------------------- 
 has password?   yes                             
--------------- -------------------------------- 
 realname        Spike-dir                       
--------------- -------------------------------- 
 email           dir@dir.com                     
--------------- -------------------------------- 
 public_key                                      
--------------- -------------------------------- 
 admin           on                              
--------------- -------------------------------- 
 repository                                      
==================================================

>>> _cd = ConfigDatabase.from_string("[user:a]\\nadmin=true", )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("admin user add")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("admin user add 'new user' 'thisispassword'") is not None
True
>>> _sc.run("admin user add 'new user' 'thisispassword'")
Traceback (most recent call last):
...
KeyError: "'new user' already exists."


>>> _cfg = "[user:dir]"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, window_size=(40, 50, ))
>>> _sc.run("user remove") is not None
True


>>> _cfg = "[user:dir]"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("user rename")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("user rename 'new name'") is not None
True
>>> _cd.has_user("dir")
False
>>> _cd.has_user("new name")
True


>>> _cfg = "[user:dir]\\npassword=1\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("password")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("password new-password") is not None
True
>>> _cd.get_user_property("dir", "password", ) == ConfigDatabase.encrypt_password("new-password")
True


>>> _cfg = "[user:a]\\nemail=a@a.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("email")
('a@a.com',)
>>> _sc.run("email b@b.com") is not None
True
>>> _cd.get_user_property("a", "email", ) == "b@b.com"
True


>>> _cfg = "[user:dir]\\nrealname=nothing\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("realname")
('nothing',)
>>> _sc.run("realname 'new name'") is not None
True
>>> _cd.get_user_property("dir", "realname", ) == 'new name'
True



>>> _cfg = "[user:dir]\\npublic_key=%s\\n" % PUBLIC_KEY
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("public_key")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("public_key view") == (PUBLIC_KEY, )
True


>>> _cfg = "[user:dir]\\npublic_key=%s\\n" % PUBLIC_KEY
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("public_key save")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument


>>> _sc.run("public_key save %s" % PUBLIC_KEY0, ) is not None
True
>>> _sc.run("public_key view") == (PUBLIC_KEY0, )
True

>>> _cfg = "[user:dir]\\npublic_key=%s\\n" % PUBLIC_KEY
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("dir", _cd, )
>>> _sc.run("public_key remove") is not None
True
>>> _sc.run("public_key view")
('',)

>>> _cfg = "[user:user-a]\\nrealname=AAA\\nemail=a@a.com\\nadmin = on\\n[user:user-b]\\nrealname=b@b.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("user-a", _cd, )
>>> print "\\n".join(_sc.run("admin user list"))
====================================================================================================
 username   realname          is admin?                                                            
========== ================= ===================================================================== 
 user-a     "AAA" <a@a.com>   O                                                                    
---------- ----------------- --------------------------------------------------------------------- 
 user-b     b@b.com           X                                                                    
====================================================================================================

>>> _cfg = "[user:user-a]\\nrealname=AAA\\nemail=a@a.com\\nadmin = on\\n[user:user-b]\\nrealname=b@b.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("user-a", _cd, )
>>> print "\\n".join(_sc.run("admin user search a"))
====================================================================================================
 username   realname          is admin?                                                            
========== ================= ===================================================================== 
 user-a     "AAA" <a@a.com>   O                                                                    
====================================================================================================


>>> print "\\n".join(_sc.run("admin user search .com"))
====================================================================================================
 username   realname          is admin?                                                            
========== ================= ===================================================================== 
 user-a     "AAA" <a@a.com>   O                                                                    
---------- ----------------- --------------------------------------------------------------------- 
 user-b     b@b.com           X                                                                    
====================================================================================================


>>> _cfg = "[user:a]\\nadmin=on\\n[repository:/a]\\npath=/a\\ndescription=Wow\\n[repository:/b]\\npath=/c\\ndescription=Call Me\\n[user:a]\\nrepository=/a\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("a", _cd, )
>>> print "\\n".join(_sc.run("repo list"))
====================================================================================================
 path   alias      is remote?                                                                      
====== ========== ================================================================================ 
 /a     /a (Wow)    X                                                                              
====================================================================================================

>>> print "\\n".join(_sc.run("admin repo list"))
====================================================================================================
 path   alias          is remote?                                                                  
====== ============== ============================================================================ 
 /c     /b (Call Me)    X                                                                          
------ -------------- ---------------------------------------------------------------------------- 
 /a     /a (Wow)        X                                                                          
====================================================================================================

>>> _cd = ConfigDatabase.from_string("[user:a]\\nadmin=true", )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("admin repo add")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("admin repo add 'al'")
Traceback (most recent call last):
...
BAD_ARGUMENT: '/al' is not directory, check it.

>>> _sc.run("admin repo add /tmp/ 'al' ") and None
>>> _cd.has_repository("/al")
True
>>> _cd.get_repository_property("/al", "path")
'/tmp'
>>> _sc.run("admin repo add /tmp/ 'al'")
Traceback (most recent call last):
...
KeyError: "'/al' already exists."

>>> _cd = ConfigDatabase.from_string("[user:a]\\nadmin=on\\n[repository:/a]", )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("admin repo remove")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("admin repo remove /a") is not None
True
>>> _cd.has_repository("a")
False

>>> _cfg = "[user:a]\\nadmin=on\\n[repository:/a]"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("admin repo rename")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("admin repo rename /a '/new name'") is not None
True
>>> _cd.has_repository("/a")
False
>>> _cd.has_repository("/new name")
True


>>> _cfg = "[user:a]\\nadmin=on\\n[repository:/a]\\n[user:aa]"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("admin repo allow user")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("admin repo allow user a aa")
Traceback (most recent call last):
...
KeyError: "'aa' does not exist."

>>> _sc.run("admin repo allow user aa a") and None
>>> _cd.get_user_property("aa", "repository", )
['a']


>>> _cfg = "[user:a]\\nadmin=on\\n[repository:/a]\\n[user:aa]\\nrepository=/a"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("admin repo disallow user")
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument
>>> _sc.run("admin repo disallow user a aa")
Traceback (most recent call last):
...
KeyError: "'aa' does not exist."

>>> _sc.run("admin repo disallow user aa /a") and None
>>> _cd.get_user_property("aa", "repository", )
[]

>>> _cfg = "[user:a]\\nadmin=on\\n[repository:/a]\\npath=/tmp"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _sc = ShellCommand("a", _cd, )
>>> _sc.run("admin repo add remote svn+ssh://dev/tmp/test_svn_repo/", )
Traceback (most recent call last):
...
NOT_ENOUGH_ARGUMENT: not enough argument

>>> _sc.run("admin repo add remote svn+ssh://dev/tmp/test_svn_repo/ this-is-password", ) and None
Traceback (most recent call last):
...
BAD_ARGUMENT: `user` must be set, like `<user>@<host>`

>>> _sc.run("admin repo add remote svn+ssh://ekips@dev/tmp/test_svn_repo/ this-is-password", ) and None
>>> _cd.has_repository("/tmp/test_svn_repo/")
True
>>> _cd.get_repository_property("/tmp/test_svn_repo/", "password", )
'this-is-password'
>>> print "\\n".join(_sc.run("admin repo list"))
====================================================================================================
 path                                     alias                is remote?                          
======================================== ==================== ==================================== 
 /tmp                                     /a                    X                                  
---------------------------------------- -------------------- ------------------------------------ 
 svn+ssh://ekips@dev/tmp/test_svn_repo/   /tmp/test_svn_repo    O                                  
====================================================================================================

>>> _sc.run("admin repo remove /tmp/test_svn_repo") and None
>>> _cd.has_repository("/tmp/test_svn_repo/")
False

>>> _sc.run("admin repo add remote svn+ssh://ekips@dev:2020/tmp/test_svn_repo/ this-is-password /alias this is description", ) and None
>>> _cd.has_repository("/alias")
True
>>> print "\\n".join(_sc.run("admin repo list"))
====================================================================================================
 path                                          alias                          is remote?           
============================================= ============================== ===================== 
 svn+ssh://ekips@dev:2020/tmp/test_svn_repo/   /alias (this is description)    O                   
--------------------------------------------- ------------------------------ --------------------- 
 /tmp                                          /a                              X                   
====================================================================================================


"""



if __name__ == "__main__" :
    import doctest
    doctest.testmod()


