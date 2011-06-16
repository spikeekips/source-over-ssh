# -*- coding: utf-8 -*-


"""
>>> from sos.config_db import ConfigDatabase

>>> _cd = ConfigDatabase.from_string("")
>>> _cd.add_user("a0", password=1, public_key=2, ) and None
>>> _cd.rename_section("user:a0", "user:a1") and None
>>> _cfg = "[user:dir0]\\npassword = thisispassword0\\nrealname = Spike-dir0\\nemail = dir0@dir.com\\npublic_key  = AAA\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )

>>> _cfg = "[user:dir0]\\npassword = thisispassword0\\nrealname = Spike-dir0\\nemail = dir0@dir.com\\npublic_key  = AAA\\n[user:dir]\\npassword = thisispassword\\nrealname = Spike-dir\\nemail = dir@dir.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )

>>> _cd.has_user("dir")
True
>>> _cd.remove_user("dir") and None
>>> _cd.has_user('dir')
False
>>> _cfg = "[user:dir]\\npassword = thisispassword\\nrealname = Spike-dir\\nemail = dir@dir.com\\nrepository="
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _cd.users
['dir']
>>> _cd.get_user_property("dir", "password")
'thisispassword'
>>> _cd.get_user_property("dir", "realname")
'Spike-dir'
>>> _cd.get_user_property("dir", "email")
'dir@dir.com'
>>> _cd.get_user_property("dir", "public_key") is None
True
>>> _cd.get_user_property("dir", "repository")
[]

>>> _cfg = "[user:dir0]\\nrepository = a,b,c\\npassword = thisispassword0\\nrealname = Spike-dir0\\nemail = dir0@dir.com\\npublic_key  = AAA\\n[user:dir]\\npassword = thisispassword\\nrealname = Spike-dir\\nemail = dir@dir.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _cd.get_user_property("dir0", "password")
'thisispassword0'
>>> _cd.get_user_property("dir0", "realname")
'Spike-dir0'
>>> _cd.get_user_property("dir0", "email")
'dir0@dir.com'
>>> _cd.get_user_property("dir0", "public_key")
'AAA'
>>> _cd.get_user_property("dir0", "repository")
['a', 'b', 'c']
>>> _cfg = "[user:dir0]\\npassword = thisispassword0\\nrealname = Spike-dir0\\nemail = dir0@dir.com\\npublic_key  = AAA\\n[user:dir]\\npassword = thisispassword\\nrealname = Spike-dir\\nemail = dir@dir.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _cd.update_user("dir0", password=1, ) and None
>>> _cd.get_user_property("dir0", "password", ) == ConfigDatabase.encrypt_password("1")
True
>>> _cd.update_user("dir00", password=1, )
Traceback (most recent call last):
...
KeyError: "'dir00' does not exist."
>>> _cd.update_user("dir", not_exist_key=1, ) and None
>>> _cd.get_user_property("dir", "not_exist_key", )
Traceback (most recent call last):
...
KeyError: "'not_exist_key' does not exist."
>>> _cd.update_user("dir", repository="a,b,c", ) and None
>>> _cd.get_user_property("dir", "repository", )
['a', 'b', 'c']
>>> _cd.update_user("dir", repository=["a" ," b", "c", ], ) and None
>>> _cd.get_user_property("dir", "repository", )
['a', 'b', 'c']



>>> _cfg = "[user:dir0]\\npassword = thisispassword0\\nrealname = Spike-dir0\\nemail = dir0@dir.com\\npublic_key  = AAA\\n[user:dir]\\npassword = thisispassword\\nrealname = Spike-dir\\nemail = dir@dir.com\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _cd.remove_user("dir") and None
>>> _cfg = "[repository:/a]\\n[repository:/b]\\n"
>>> ConfigDatabase.from_string(_cfg, ).repositories
['/b', '/a']
>>> _cfg = "[repository:/a]\\npath=/a/b\\n[repository:/b]\\npath=/a/b/c\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )

>>> _cd.has_repository(alias="a")
True
>>> _cd.has_repository(path="/a/b/")
True
>>> _cd.has_repository(path="/a/b")
True
>>> _cd.remove_repository("/a") and None
>>> _cd.has_repository(alias="/a")
False
>>> _cfg = "[repository:/a]\\npath=/a/b\\n[repository:/b]\\npath=/a/b/c\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _cd.get_repository_property("a", "path")
'/a/b'
>>> _cd.update_repository("/a", path="/show/me/") and None
>>> _cd.get_repository_property("/a", "path")
'/show/me'
>>> _cd.get_repository_property("/a", "not_exist_key")
Traceback (most recent call last):
...
KeyError: "'not_exist_key' does not exist."
>>> _cfg = ""
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _cd.add_repository("/tmp/", "/y") and None
>>> _cd.has_repository("/y", )
True
>>> _cd.get_repository_property("/y", "path", )
'/tmp'
>>> _cfg = "[repository:/a]\\npath=/a/b\\n[repository:/b]\\npath=/a/b/c\\n"
>>> _cd = ConfigDatabase.from_string(_cfg, )
>>> _cd.rename_repository("/a", "c", ) and None
>>> _cd.has_repository("/a", )
False
>>> _cd.has_repository("/c", )
True
>>> _cd.get_repository_property("/c", "path", )
'/a/b'

>>> a = ConfigDatabase.from_string("[repository:/a]\\npath=ssh://ekips:1@localhost:220/a/b/c\\n")
>>> a.is_remote_repository("a")
True
>>> a.parse_remote_repository("a")
{'host': 'localhost', 'scheme': 'ssh', 'user': 'ekips', 'path': '/a/b/c', 'password': '1', 'port': 220}

bad remote path format,
>>> a = ConfigDatabase.from_string("[repository:/a]\\npath=ekips@localhost/a/b/c\\n")
>>> a.parse_remote_repository("a")
Traceback (most recent call last):
...
ValueError: 'a' is not remote repository path.

>>> a = ConfigDatabase.from_string("[repository:/a]\\npath=ssh://ekips@localhost/a/b/c\\n")
>>> a.parse_remote_repository("a")
{'host': 'localhost', 'scheme': 'ssh', 'user': 'ekips', 'path': '/a/b/c', 'password': None, 'port': 22}
>>> a = ConfigDatabase.from_string("[repository:/a]\\npath=ssh://ekips@localhost\\n")
>>> a.parse_remote_repository("a")
{'host': 'localhost', 'scheme': 'ssh', 'user': 'ekips', 'path': '/', 'password': None, 'port': 22}

>>> a = ConfigDatabase.from_string("[repository:/a]\\npath=ssh://localhost/a/b/c\\n")
>>> a.parse_remote_repository("a")
{'host': 'localhost', 'scheme': 'ssh', 'user': None, 'path': '/a/b/c', 'password': None, 'port': 22}

"""





if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




