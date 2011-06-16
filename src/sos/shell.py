# -*- coding: utf-8 -*-

import os
import re
import shlex
import uuid

from twisted.conch import error as error_conch, recvline
from twisted.conch.ssh.keys import Key, BadKeyError
from twisted.internet import defer, error as error_internet

import _exceptions
import utils


class SOSProtocol (recvline.HistoricRecvLine, ) :
    TERMINAL_COLOR_SUPPORTED = ("xterm", "xterm-color", "linux", )

    def __init__(self, avatar, ) :
        self._avatar = avatar
        self._config_db = self._avatar._config_db

        self._is_xterm = self._avatar._env.get("TERM", "xterm",
                ) in self.TERMINAL_COLOR_SUPPORTED

        _ms = filter(lambda f: f.startswith("command_"), dir(self))
        self._commands = [c.replace("command_", "", 1) for c in _ms]

    def connectionMade (self, ) :
        recvline.HistoricRecvLine.connectionMade(self, )

        self.keyHandlers.update({
            "\x04": self._quit,
            "\x08": self.handle_BACKSPACE,
            "\x15": self.handle_CLEAR_LINE,
        }, )

        self.write("Welcome to source+over+ssh server.")
        self._help()
        self.showPrompt()

    def initializeScreen (self, ) :
        self.setInsertMode()

    def handle_CLEAR_LINE (self, ) :
        while self.lineBufferIndex > 0 :
            self.handle_BACKSPACE()

    def write (self, s, p=False, ) :
        self.terminal.write(s)
        if not p :
            self.terminal.nextLine()

    def lineReceived (self, line, ) :
        if self._avatar._verbose and line.strip() :
            utils.debug("avatar: data received: %s" % ([line, ], ), )

        line = line.strip()
        if not line :
            self.showPrompt()
            return

        _sc = ShellCommand(
            self._avatar.username,
            self._config_db,
            is_xterm=self._is_xterm,
            window_size=self._avatar._window_size[:2],
        )
        try :
            _messages = _sc.run(line, )
        except _exceptions.CLEAR :
            self.terminal.reset()
        except _exceptions.QUIT :
            return self._quit()
        except _exceptions.PERMISSION_DENIED, e :
            self.write("error: %s" % e, )
        except Exception, e :
            if self._avatar._verbose and not isinstance(e,
                        (_exceptions.NO_SUCH_COMMAND,
                        _exceptions.NOT_ENOUGH_ARGUMENT,
                        _exceptions.BAD_ARGUMENT, )
                    ) :
                import traceback
                traceback.print_exc()

            self.write("error: %s" % e, )
            try :
                _h = _sc.run("help " + line, )
            except :
                _h = _sc.run("help")

            for i in _h :
                self.write(i, )
        else :
            if isinstance(_messages, defer.Deferred, ) :
                return _messages.addCallback(
                            lambda x : map(self.write, x, ),
                        ).addCallback(
                                lambda x : self.showPrompt(), )

            for i in _messages :
                self.write(i, )

        self.showPrompt()

    def showPrompt(self):
        _s = (self._is_xterm and "\033[01;32m%s\033[00m $ " or "%s $") % (
                self._avatar.username, )
        self.write("sso: " + _s, p=True, )

    ##################################################
    # commands
    def _quit (self, ) :
        self.terminal.loseConnection()

    def _help (self, ) :
        _sc = ShellCommand(
            self._avatar.username,
            self._config_db,
            is_xterm=self._is_xterm,
            window_size=self._avatar._window_size[:2],
        )
        for i in _sc.run("help", ) :
            self.write(i, )


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
    > admin repo add remote <remote repo uri> <password> [<alias>]
    > admin repo check <alias>
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
        "admin repo add remote":        "$ admin repo add remote <remote repo uri> <password> [<alias>] [<description>]",
        "admin repo check":             "$ admin repo check <alias>",
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
            if a[1] == "remote" :
                if len(a[2:]) < 2 :
                    raise _exceptions.NOT_ENOUGH_ARGUMENT

                _r["subcommand"] = a[:2]
                _r["args"] = tuple(a[2:], )
            else :
                _r["args"] = tuple(a[1:], )
            return _r
        elif _sub == "check" and len(a) == 2 :
            _r["args"] = (a[1], )
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

        self._is_admin = self._config_db.is_admin(self._username, )

    def run (self, line, ) :
        if shlex.split(line, )[0] == "admin" and not self._is_admin :
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
                is_admin=self._is_admin,
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

        return utils.format_data(_values, width=self._window_size[1], captions=("key", "value", ), )

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
                x,
                self._config_db.get_full_username(x),
                self._config_db.is_admin(x) and "O" or "X",
            ),
            userlist,
        )

        return [
                i for i in utils.format_data(
                    _values and _values or (("no users", "", ), ),
                    width=self._window_size[1],
                    captions=("username", "realname", "is admin?", ),
                )
        ]

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
                "%s" % (
                    self._config_db.get_repository_property(x, "path"),
                ),
                "%s%s" % (
                    x,
                    self._config_db.get_repository_property(x, "description", "").strip() and (
                        " (%s)" % self._config_db.get_repository_property(x, "description", "").strip()
                    ) or "",
                ),
                self._config_db.is_remote_repository(x) and " O" or " X",
            ),
            _repos,
        )
        #_values.sort()
        return utils.format_data(
            _values,
            width=self._window_size[1],
            captions=("path", "alias", "is remote?", ),
            num_columns=3,
        )

    def c_repo_add (self, a, **kw) :
        if len(a) < 2 :
            a = list(a)
            a.extend(a, )

        a = map(utils.normpath, a)
        if not os.path.exists(a[0], ) or not os.path.isdir(a[0], ) :
            raise _exceptions.BAD_ARGUMENT(
                    "'%s' is not directory, check it." % a[0], )

        self._config_db.add_repository(*a).save()
        _l = ["repository, '%s', alias, '%s' was added." % (a[0], a[1], ), "", ]
        _l.extend(list(self.c_repo_list(None, **kw)), )

        return tuple(_l)

    def c_repo_add_remote (self, a, **kw) :
        a = list(a)
        a.extend(["", "", ])

        (_uri, _password, _alias, ) = a[:3]
        _description = a[3:]
        _parsed = utils.parse_remote_repository(_uri, )
        if not _parsed.get("user") :
            raise _exceptions.BAD_ARGUMENT("`user` must be set, like `<user>@<host>`")

        if not _alias.strip() :
            if not self._config_db.has_repository(_parsed.get("path"), ) :
                _alias = _parsed.get("path")
            else :
                _alias = "/" + uuid.uuid1().hex

        _a = [_uri, _alias, ]
        self._config_db.add_repository(*_a, **dict(
            description=_description, password=_password, )).save()
        _l = ["remote repository, '%s', alias, '%s' was added." % (_uri, _alias, ), "", ]
        _l.extend(list(self.c_repo_list(None, **kw)), )

        return tuple(_l)

    def c_repo_check (self, a, **kw) :
        if not self._config_db.is_remote_repository(a[0]) :
            _path = self._config_db.get_repository_property(a[0], "path", )
            if not os.path.exists(_path, ) or not os.path.isdir(_path, ) :
                return ("error: '%s' is not valid repository directory, check it." % _path, )

            return ("'%s' is valid repository path." % _path, )

        _path = self._config_db.get_repository_property(a[0], "path", )
        _parsed = utils.parse_remote_repository(_path, )

        from ssh_factory import SSHClient
        _client = SSHClient(
            None,
            _parsed.get("host"),
            _parsed.get("port", ),
            _parsed.get("user"),
            self._config_db.get_repository_property(a[0], "password", None, ),
        )

        def _cb_open_session (r, ) :
            _client.close()
            return ("remote repository, '%s'('%s') is accessible." % (a[0], _path, ), )

        def _eb_open_session (f, ) :
            _client.close()
            _r = ["error: remote repository, '%s'('%s') can not be accessible." % (a[0], _path, ), ]

            _e = None
            if f.check(error_internet.DNSLookupError, ) :
                _e = f.value.message
            elif f.check(error_conch.ConchError, ) :
                _e = "authentication failed, check the username or password."

            if _e :
                _r.append("\t- %s" % _e)

            return _r

        return _client.connect().addCallbacks(_cb_open_session, _eb_open_session, )

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
