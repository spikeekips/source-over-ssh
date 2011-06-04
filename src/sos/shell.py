# -*- coding: utf-8 -*-

import shlex
import re

from twisted.conch.ssh.keys import Key, BadKeyError

import _exceptions
import utils


class BaseCommandParser (object, ) :
    helps = {
        "help": "print help. $ help [<command>]",
    }

    def __init__ (self, command, ) :
        self._command = command

        self._commands_in_helps = None
        self._helps_combined = None

        self._commands_in_helps = list()
        self._helps_combined = dict()
        self.parse_helps()

    def parse_helps (self, ) :
        for i, j in self.helps.items() :
            _f = shlex.split(i, )
            if _f[0] not in self._commands_in_helps :
                self._commands_in_helps.append(_f[0], )

            for x in range(len(_f) - 1, -1, -1, ) :
                _s = " ".join(_f[:x])
                self._helps_combined.setdefault(_s, list(), )
                self._helps_combined[_s].append((i, j, ), )

    def parse (self, ) :
        _a = shlex.split(self._command, )
        try :
            _c, _args, = _a[0], _a[1:]
        except IndexError :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        _r = self.get_command_method(_c, )(_args, )
        if "command" not in _r :
            _r["command"] = [_c, ]

        if "subcommand" in _r :
            if type(_r["subcommand"]) in (str, ) :
                _r["subcommand"] = [_r["subcommand"], ]
            _r["command"] = tuple(_r["command"] + _r["subcommand"], )
            del _r["subcommand"]

        return _r

    def get_help (self, command=None, ) :
        if command is None :
            return (
                (
                    "COMMANDS", "%s" % ", ".join(
                        map(lambda x : "'%s'" % x,
                            set(self._commands_in_helps, ), ),
                    ),
                ),
            )

        if type(command) in (str, ) :
            command = shlex.split(command, )

        _l = None
        for i in range(len(command) - 1, -1, -1) :
            _command = " ".join(command[:i + 1], )
            if _command in self.helps :
                _l = (
                    (_command, self.helps.get(_command, ), ),
                )
                break
            elif _command in self._helps_combined :
                _l = self._helps_combined.get(_command, )
                break

        if _l is None :
            raise _exceptions.NO_SUCH_COMMAND

        _l = list(_l, )
        _l.sort()
        _l = tuple(_l, )
        return _l

    def get_command_method (self, command, ) :
        try :
            return getattr(self, "c_%s" % command, )
        except AttributeError :
            raise _exceptions.NO_SUCH_COMMAND

    def c_help (self, a, ) :
        if len(a) < 1 :
            return dict()

        return dict(args=tuple(a, ), )


class CommandParser (BaseCommandParser, ) :
    """
    ##################################################
    command examples
    ##################################################

    > help [<command>]

    normal user commands
    ==================================================

    > user view

    > user remove
    > user rename <new name>

    > password <new password>
    > email [<email>]
    > realname [<real name>]

    > public_key view
    > public_key save <key>
    > public_key remove

    > repo list
    """

    helps = {
        "quit":                 "quit $ quit",
        "clear":                "clear $ clear",
        "user view":            "view user information. $ user view",
        "user remove":          "remove user. $ user remove",
        "user rename":          "rename username. $ user rename <new name>",
        "password":             "set password. $ password <new password>",
        "email":                "view or set email. $ email [<email>]",
        "realname":             "view or set realname. $ realname [<real name>]",
        "public_key view":      "view public key. $ public_key view",
        "public_key save":      "save public key. $ public_key save <key>",
        "public_key remove":    "remove public key. $ public_key remove",
        "repo list":            "show all repositories. $ repo list",
    }
    helps.update(BaseCommandParser.helps, )

    def __init__ (self, *a, **kw) :
        self._is_admin = kw.get("is_admin", False, )
        if "is_admin" in kw :
            del kw["is_admin"]

        super(CommandParser, self).__init__(*a, **kw)

        if self._is_admin :
            self._commands_in_helps.append("admin", )

    def c_quit (self, a, ) :
        if len(a) > 0 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        return dict()

    def c_clear (self, a, ) :
        if len(a) > 0 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        return dict()

    def c_password (self, a, ) :
        if len(a) == 1 :
            return dict(
                args=(a[0], ),
            )

        raise _exceptions.NOT_ENOUGH_ARGUMENT

    def c_user (self, a, ) :
        if len(a) < 1 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        _sub = a[0]
        _r = dict(subcommand=_sub, )

        if _sub in ("remove", "view", ) :
            if len(a) != 1 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT
        elif _sub == "rename" :
            if len(a) != 2 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT

            _r["args"] = (a[1], )
        else :
            raise _exceptions.BAD_ARGUMENT

        return _r

    # from `django.core.validators`
    email_re = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
        r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$', re.IGNORECASE, )  # domain

    def c_email (self, a, ) :
        if len(a) < 1 :
            return dict()

        if len(a) == 1 :
            if not self.email_re.match(a[0], ) :
                raise _exceptions.BAD_ARGUMENT("invalid email address.")

            return dict(
                args=(a[0], ),
            )

        raise _exceptions.NOT_ENOUGH_ARGUMENT

    def c_realname (self, a, ) :
        if len(a) < 1 :
            return dict()

        return dict(
            args=tuple(a, ),
        )

    def _check_public_key (self, key, ) :
        try :
            Key.fromString(data=key, )
        except BadKeyError :
            raise _exceptions.BAD_ARGUMENT("invalid public key.")

        return key.strip()

    def c_public_key (self, a, ) :
        if len(a) < 1 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        _sub = a[0]
        _r = dict(subcommand=_sub, )

        if _sub in ("view", "remove", ) :
            if len(a) != 1 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT
        elif _sub == "save" :
            if len(a) < 2 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT

            _r["args"] = (self._check_public_key(" ".join(a[1:]), ), )
        else :
            raise _exceptions.BAD_ARGUMENT

        return _r

    def c_repo (self, a, ) :
        if len(a) < 1 :
            return dict()

        if len(a) == 1 :
            if a[0] == "list" :
                return dict(subcommand=a[0], )

            raise _exceptions.BAD_ARGUMENT

        raise _exceptions.NOT_ENOUGH_ARGUMENT

    def c_admin (self, a, ) :
        _r = AdminCommandParser(utils.shlex_combine(a), ).parse()
        _r["admin"] = True

        return _r


class AdminCommandParser (CommandParser, ) :
    """
    ##################################################
    command examples
    ##################################################

    admin commands
    ==================================================

    > admin repo list
    > admin repo add <repo path> [<alias>]
    > admin repo remove <alias>
    > admin repo rename <alias> <new alias>
    > admin repo allow user <username> <alias>
    > admin repo disallow user <username> <alias>

    > admin user list
    > admin user search <keyword>
    > admin user view <username>

    > admin user add <username> <password>
    > admin user remove <username>
    > admin user rename <username> <new name>

    > admin email <username> [<email>]
    > admin realname <username> [<email>]

    > admin public_key view <username>
    > admin public_key save <username> <key>
    > admin public_key remove <username>

    > admin password <username> <new password>

    """

    helps = {
        "admin repo list":              "$ admin repo list",
        "admin repo add":               "$ admin repo add <repo path> [<alias>] [<description>]",
        "admin repo remove":            "$ admin repo remove <alias>",
        "admin repo rename":            "$ admin repo rename <alias> <new alias>",
        "admin repo allow user":        "$ admin repo allow user <username> <alias>",
        "admin repo disallow user":     "$ admin repo disallow user <username> <alias>",
        "admin repo user list":         "$ admin repo user list <alias>",
        "admin user list":              "$ admin user list",
        "admin user search":            "$ admin user search <keyword>",
        "admin user view":              "$ admin user view <username>",
        "admin user add":               "$ admin user add <username> <password>",
        "admin user remove":            "$ admin user remove <username>",
        "admin user rename":            "$ admin user rename <username> <new name>",
        "admin email":                  "$ admin email <username> [<email>]",
        "admin realname":               "$ admin realname <username> [<email>]",
        "admin public_key view":        "$ admin public_key view <username>",
        "admin public_key save":        "$ admin public_key save <username> <key>",
        "admin public_key remove":      "$ admin public_key remove <username>",
        "admin password":               "$ admin password <username> <new password>",
    }

    def __init__ (self, *a, **kw) :
        super(AdminCommandParser, self, ).__init__(*a, **kw)

        self._commands_in_helps = list()

    def c_repo (self, a, ) :
        try :
            return super(AdminCommandParser, self, ).c_repo(a, )
        except :
            pass

        if len(a) < 1 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        _sub = a[0]
        _r = dict(subcommand=_sub, )
        if _sub == "add" and len(a) > 1 :
            _r["args"] = tuple(a[1:], )
            return _r
        elif _sub == "remove" and len(a) == 2 :
            _r["args"] = (a[1], )
            return _r
        elif _sub == "rename" and len(a) == 3 :
            _r["args"] = tuple(a[1:], )
            return _r
        elif _sub == "user" and len(a) == 3 and a[1] == "list" :
            _r["subcommand"] = a[:2]
            _r["args"] = tuple(a[2:], )
            return _r
        elif _sub in ("allow", "disallow",
                ) and len(a) == 4 and a[1] == "user" :
            _r["subcommand"] = a[:2]
            _r["username"] = a[2]
            _r["args"] = tuple(a[3:], )
            return _r

        raise _exceptions.NOT_ENOUGH_ARGUMENT

    re_username = re.compile("^[\w\-][\w\-]*$", re.I, )

    def c_user (self, a, ) :
        if len(a) < 1 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        _sub = a[0]
        _r = dict(subcommand=_sub, )
        if _sub == "list" :
            return _r
        elif _sub in ("search", ) :
            if len(a) != 2 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT

            _r["args"] = (a[1], )
            return _r
        elif _sub in ("view", "remove", ) :
            if len(a) != 2 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT

            _r["username"] = a[1]
            return _r
        elif _sub in ("add", "rename", ) :
            if len(a) != 3 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT

            if _sub == "add" :
                _names = (a[0], )
            elif _sub == "rename" :
                _names = tuple(a[1:], )

            if False in map(lambda x : bool(self.re_username.match(x), ), _names, ) :
                raise _exceptions.BAD_ARGUMENT("invalid username.")

            _r["username"] = a[1]
            _r["args"] = (a[2], )
            return _r

        raise _exceptions.BAD_ARGUMENT

    def c_email (self, a, ) :
        if len(a) < 1 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        if len(a) == 1 :
            return dict(username=(a[0], ), )
        elif len(a) == 2 :
            if not self.email_re.match(a[1], ) :
                raise _exceptions.BAD_ARGUMENT("invalid email address.")

            return dict(
                username=a[0],
                args=(a[1], ),
            )

        raise _exceptions.NOT_ENOUGH_ARGUMENT

    def c_realname (self, a, ) :
        if len(a) < 1 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        if len(a) == 1 :
            return dict(username=a[0], )
        elif len(a) == 2 :
            return dict(
                username=a[0],
                args=(a[1], ),
            )

        raise _exceptions.NOT_ENOUGH_ARGUMENT

    def c_public_key (self, a, ) :
        if len(a) < 1 :
            raise _exceptions.NOT_ENOUGH_ARGUMENT

        _sub = a[0]
        _r = dict(subcommand=_sub, )

        if _sub in ("view", "remove", ) :
            if len(a) != 2 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT
            _r["username"] = a[1]
        elif _sub == "save" :
            if len(a) < 3 :
                raise _exceptions.NOT_ENOUGH_ARGUMENT

            _r["username"] = a[1]
            _r["args"] = (self._check_public_key(" ".join(a[2:]), ), )
        else :
            raise _exceptions.BAD_ARGUMENT

        return _r

    def c_password (self, a, ) :
        if len(a) == 2 :
            return dict(
                username=a[0],
                args=(a[1], ),
            )

        raise _exceptions.NOT_ENOUGH_ARGUMENT


class ShellCommand (object, ) :
    def __init__ (self,
                username,
                config_db,
                is_xterm=False,
                window_size=(50, 100, ),
            ) :
        self._username = username
        self._config_db = config_db
        self._is_xterm = is_xterm
        self._window_size = window_size

    def run (self, line, ) :
        if shlex.split(line, )[0] == "admin" and not self._config_db.is_admin(self._username, ) :
            raise _exceptions.PERMISSION_DENIED

        _parsed = CommandParser(line, ).parse()
        _parsed.setdefault("username", self._username, )
        _parsed.setdefault("admin", False, )

        _command = "_".join(_parsed.get("command"))
        try :
            return getattr(self, "c_%s" % _command, )(
                _parsed.get("args", tuple(), ),
                **_parsed
            )
        except AttributeError :
            import traceback
            traceback.print_exc()
            raise _exceptions.NO_SUCH_COMMAND

    ################################################################################
    # commands
    def c_clear (self, a, **kw) :
        raise _exceptions.CLEAR

    def c_quit (self, a, **kw) :
        raise _exceptions.QUIT

    def c_help (self, a, **kw) :
        _l = None
        if len(a) < 1 :
            _l = CommandParser(
                None,
                is_admin=self._config_db.is_admin(self._username, ),
            ).get_help()

        if _l is None :
            try :
                _l = CommandParser(None, ).get_help(a, )
            except _exceptions.NO_SUCH_COMMAND :
                pass

        if _l is None :
            try :
                _l = AdminCommandParser(None, ).get_help(" ".join(a, ), )
            except _exceptions.NO_SUCH_COMMAND :
                pass

        if _l :
            _l = list(_l)
            return ["", "usage:", ] + [
                i for i in utils.format_help(_l, width=self._window_size[1], delm="", )
            ] + ["", ]

        raise _exceptions.NO_SUCH_COMMAND

    def c_user_view (self, a, username, **kw) :
        _values = map(
            lambda x : (x, self._config_db.get_user_property(username, x, "", ), ),
            ("realname", "email", "public_key", "admin", ),
        )
        _values.insert(0,
            (
                "has password?",
                bool(self._config_db.get_user_property(username, "password")) and "yes" or "no",
            ),
        )
        _values.insert(0, ("username", username, ), )
        _respositories = self._config_db.get_user_property(username, "repository", )
        _values.append(("repository", _respositories and ", ".join(_respositories) or "", ), )

        return utils.format_data(_values, width=self._window_size[1], )

    def c_user_add (self, a, username, **kw) :
        self._config_db.add_user(username, password=a[0], ).save()
        return ("user, '%s' was added." % username, )

    def c_user_remove (self, a, username, **kw) :
        self._config_db.remove_user(username, ).save()
        return ("user, '%s' removed" % username, )

    def c_user_rename (self, a, username, **kw) :
        self._config_db.rename_user(username, a[0], ).save()
        return ("user, '%s' changed to '%s'" % (username, a[0], ), )

    def c_password (self, a, username, **kw) :
        self._config_db.update_user(username, password=a[0], ).save()
        return ("updated password. ", )

    def c_email (self, a, username, **kw) :
        if len(a) < 1 :
            return (self._config_db.get_user_property(username, "email", ), )

        self._config_db.update_user(username, email=a[0], ).save()
        return ("updated email. ", )

    def c_realname (self, a, username, **kw) :
        if len(a) < 1 :
            return (self._config_db.get_user_property(username, "realname", ), )

        self._config_db.update_user(username, realname=" ".join(a), ).save()
        return ("updated realname. ", )

    def c_public_key_view (self, a, username, **kw) :
        return (self._config_db.get_user_property(username, "public_key", "", ), )

    def c_public_key_save (self, a, username, **kw) :
        self._config_db.update_user(username, public_key=a[0], ).save()
        return ("updated public key.", )

    def c_public_key_remove (self, a, username, **kw) :
        self._config_db.update_user(username, public_key=None, ).save()
        return ("remove public key.", )

    def print_user_list (self, userlist, ) :
        _values = map(
            lambda x : (
                self._config_db.is_admin(x) and ("%s *" % x) or x,
                self._config_db.get_full_username(x),
            ),
            userlist,
        )

        _l = [i for i in utils.format_data(
            _values and _values or (("no users", "", ), ),
            width=self._window_size[1], )]

        if _values :
            _l.append("(* is `admin`)", )

        return _l

    def c_user_list (self, a, **kw) :
        return self.print_user_list(self._config_db.users, )

    def c_user_search (self, a, **kw) :
        return self.print_user_list(self._config_db.search_user(a[0]), )

    def c_repo_list (self, a, username, **kw) :
        if kw.get("admin") :  # show all repository
            _repos = self._config_db.repositories
        else :
            _repos = self._config_db.get_user_property(username, "repository", list(), )

        _values = map(
            lambda x : (
                self._config_db.get_repository_property(x, "path"),
                "%s%s" % (
                    x,
                    self._config_db.get_repository_property(x, "description", "").strip() and (
                        " (%s)" % self._config_db.get_repository_property(x, "description", "").strip()
                    ) or "",
                ),
            ),
            _repos,
        )
        _values.sort()
        return utils.format_data(_values, width=self._window_size[1], )

    def c_repo_add (self, a, **kw) :
        if len(a) < 2 :
            a = list(a)
            a.extend(a, )

        self._config_db.add_repository(*a).save()
        _l = ["repository, '%s', alias, '%s' was added." % (a[0], a[1], ), "", ]
        _l.extend(list(self.c_repo_list(None, **kw)), )

        return tuple(_l)

    def c_repo_remove (self, a, **kw) :
        self._config_db.remove_repository(a[0], ).save()
        return ("repository, '%s' was removed." % a[0], )

    def c_repo_rename (self, a, **kw) :
        a = map(utils.normpath, a, )
        self._config_db.rename_repository(*a).save()
        return ("repository, '%s' changed to '%s'" % (a[0], a[1], ), )

    def c_repo_allow_user (self, a, username, **kw) :
        _alias = a[0]
        if not self._config_db.has_repository(alias=_alias, ) :
            raise KeyError("'%s' does not exist." % _alias, )

        _l = self._config_db.get_user_property(username, "repository", list(), )
        if _alias in _l :
            raise KeyError("'%s' was already allowed." % _alias, )

        _l.append(_alias, )
        self._config_db.update_user(username, repository=_l, ).save()
        return ("repository, '%s' allowed to user, '%s'" % (_alias, username, ), )

    def c_repo_disallow_user (self, a, username, **kw) :
        _alias = a[0]
        if not self._config_db.has_repository(alias=_alias, ) :
            raise KeyError("'%s' does not exist." % _alias, )

        _l = self._config_db.get_user_property(username, "repository", list(), )
        if _alias not in _l :
            raise KeyError("'%s' was not allowed." % _alias, )

        del _l[_l.index(_alias, )]
        self._config_db.update_user(username, repository=_l, ).save()
        return ("repository, '%s' disallowed to user, '%s'" % (_alias, username, ), )

    def c_repo_user_list (self, a, **kw) :
        _alias = a[0]
        if not self._config_db.has_repository(alias=_alias, ) :
            raise KeyError("'%s' does not exist." % _alias, )

        _users = list()
        for i in self._config_db.users :
            _l = self._config_db.get_user_property(i, "repository", list(), )
            if _alias not in _l :
                continue
            _users.append(i, )

        return self.print_user_list(_users, )
