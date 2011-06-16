# -*- coding: utf-8 -*-


import re
import shlex
import string
import urlparse

from twisted.internet import defer, error as error_internet

import _base
import _exceptions
import ssh_factory
import utils


class SessionTunnel (_base.BaseSessionTunnel, ) :
    name = "svn"

    _buf = list()

    def __init__ (self, *a, **kw) :
        super(SessionTunnel, self).__init__(*a, **kw)

        self._buf = list()

    def parse_exec (self, ) :
        _parsed = shlex.split(self._commandline, )

        _argv = list()
        for i in _parsed :
            if i.startswith("--tunnel-user=") :
                continue
            _argv.append(i, )

        _argv.append("--tunnel-user='%s'" % (
            self._config_db.get_full_username(self._session.avatar.username, ), ),
        )

        return " ".join(_argv, )

    def parse_to_server (self, data, ) :
        try :
            _cp = SVNCommandParser(data, )
        except _exceptions.BAD_SVN_REPOSITORY_COMMAND :
            return data

        if not self._alias :
            (self._alias, self._repo_server_base,
                    ) = self._parse_repository(_cp, )

            self._repo_client_base = _cp.get_client_base(self._alias, )
            self._is_remote = self._config_db.is_remote_repository(self._alias, )
            if self._is_remote :
                _parsed = self._config_db.parse_remote_repository(
                        self._alias, )

                def _cb_open_session (r, ) :
                    self._client.open_session(self._commandline, )
                    self._client.dataReceived = self._session.write
                    return

                def _eb_open_session (f, ) :
                    if f.check(error_internet.ConnectionRefusedError, ) :
                        self._session.loseConnection()

                self._client = ssh_factory.SSHClient(
                    self._session,
                    _parsed.get("host"),
                    _parsed.get("port", ),
                    _parsed.get("user"),
                    self._config_db.get_repository_property(self._alias, "password", None, ),
                )
                self._client.connect().addCallbacks(_cb_open_session, _eb_open_session, )
                self._buf.append(self.replace_path_to_server(_cp, ), )
                return None

        return self.replace_path_to_server(_cp, )

    def to_server (self, data, ) :
        _d = defer.maybeDeferred(super(SessionTunnel, self, ).to_server, data, )
        if self._client :
            _d.addCallback(self._client.write, )

        return _d

    _is_first_line_to_client = True

    def to_client (self, data, ) :
        if self._client and self._is_first_line_to_client :
            self._is_first_line_to_client = False
            map(self._client.write, self._buf)
            self._buf = None
            return None

        return super(SessionTunnel, self, ).to_client(data, )

    def _parse_repository (self, cp, ) :
        if self._avatar._is_admin :
            _available_repos = self._config_db.repositories
        else :
            _available_repos = self._config_db.get_user_property(
                self._avatar.username, "repository", list(), )

        _alias = cp.get_alias(_available_repos, )
        if not _alias :
            _msg = "not allowed this repository, `%s` to user, '%s'" % (
                cp.get_repository_path(),
                self._avatar.username,
            )
            utils.debug(_msg, )
            raise _exceptions.PERMISSION_DENIED(_msg, )

        _repo_server_base = self._config_db.get_repository_property(
                _alias, "path", )

        return (_alias, _repo_server_base, )

    def parse_to_client (self, data, ) :
        try :
            _cp = SVNCommandParser(data, )
        except _exceptions.BAD_SVN_REPOSITORY_COMMAND :
            return data

        return self.replace_path_to_client(_cp, )

    def replace_path_to_server (self, cp, ) :
        if self._is_remote :
            return cp.replace_repository(self._repo_client_base, self._repo_server_base, )
        else :
            return cp.replace_path(self._alias, self._repo_server_base, )

    def replace_path_to_client (self, cp, ) :
        if self._is_remote :
            return cp.replace_repository(self._repo_server_base, self._repo_client_base, )
        else :
            return cp.replace_path(self._repo_server_base, self._alias, )


class SVNCommandParser (object, ) :
    _strings = re.escape("".join([i for i in string.punctuation if i not in (")", "(", )], ), )

    IS_SVN_COMMAND = re.compile("^[\s]*\([\s]*.*[\s]*\)[\s]*$", )
    RE_REPOSITORY_WITH_LEN = re.compile("[\s]*(\d+):(svn\+ssh\:\/\/[\w%s]+)[\s]*" % _strings, re.I, )
    RE_REPOSITORY_QUOTED = re.compile("[\s]*(')(svn\+ssh\:\/\/[\w%s]+)'[\s]*" % _strings, re.I, )

    _COMMANDS_HAS_REPOSITORY = {
        "edit-pipeline": ("^[\s]*\([\s]*\d+[\s]*\([\s]*(?P<type>edit-pipeline).*\)", RE_REPOSITORY_WITH_LEN, ),
        "success": ("^[\s]*\([\s]*(?P<type>success)[\s]*\(", RE_REPOSITORY_WITH_LEN, ),
        "failure": ("^[\s]*\([\s]*(?P<type>failure)[\s*]\(", RE_REPOSITORY_QUOTED, ),
        "reparent": ("^\([\s]*(?P<type>reparent)[\s]*\(", RE_REPOSITORY_WITH_LEN, ),
        "open-root": ("^[\s]*\([\s]*(?P<type>open-root)[\s]*\(", RE_REPOSITORY_WITH_LEN, ),
        "add-dir": ("^[\s]*\([\s]*(?P<type>add-dir)[\s]*\(", RE_REPOSITORY_WITH_LEN, ),
    }

    COMMANDS_HAS_REPOSITORY = dict(
        map(
            lambda x : (x[0], (re.compile(x[1][0], re.I, ), x[1][1], ), ),
            _COMMANDS_HAS_REPOSITORY.items(),
        ),
    )

    def __init__ (self, command, ) :
        self._command = command

        self._parse()

    def _parse (self, ) :
        self._r = None
        if not self.IS_SVN_COMMAND.match(self._command, ) :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

        _re_repository = None
        for i, j in self.COMMANDS_HAS_REPOSITORY.items() :
            if j[0].search(self._command, ) is None :
                continue
            elif j[1].search(self._command, ) is None :
                continue

            _re_repository = i

        if _re_repository is None :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

        self._r = _re_repository

    def get_client_base (self, alias, ) :
        if self._r is None :
            return None

        _alias = utils.normpath(alias, )
        _base = None

        (_none, _r, ) = self.COMMANDS_HAS_REPOSITORY.get(self._r, )
        if _r == self.RE_REPOSITORY_WITH_LEN :
            _re_repo = list(_r.finditer(self._command, ), )
            for j in range(len(_re_repo) - 1, -1, -1, ) :
                i = _re_repo[j]
                _parsed = list(urlparse.urlsplit(i.group(2), ), )
                _parsed[2] = _alias
                _base = urlparse.urlunsplit(_parsed, )
                break

        elif _r == self.RE_REPOSITORY_QUOTED :
            _re_repo = list(_r.finditer(self._command, ), )
            for j in range(len(_re_repo) - 1, -1, -1, ) :
                i = _re_repo[j]
                _parsed = list(urlparse.urlsplit(i.group(2), ), )
                _parsed[2] = _alias
                _base = urlparse.urlunsplit(_parsed, )
                break

        else :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

        return _base

    def replace_repository (self, a, b, ) :
        if self._r is None :
            return self._command

        (_none, _r, ) = self.COMMANDS_HAS_REPOSITORY.get(self._r, )
        if _r == self.RE_REPOSITORY_WITH_LEN :
            _method = self._replace_repository_with_len
        elif _r == self.RE_REPOSITORY_QUOTED :
            _method = self._replace_repository_quoted
        else :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

        return _method(_r, a, b, )

    def _replace_repository_with_len (self, r, a, b, ) :
        _re_repo = list(r.finditer(self._command, ), )

        _command = self._command
        for j in range(len(_re_repo) - 1, -1, -1, ) :
            i = _re_repo[j]

            _new_path = re.compile(
                "^(%s)" % (re.escape(a, ), ),
            ).sub(b, i.group(2), )

            _command = "%s%s%s" % (_command[:i.start(1)], len(_new_path), _command[i.end(1):], )
            _command = "%s%s%s" % (_command[:i.start(2)], _new_path, _command[i.end(2):], )

        return _command

    def _replace_repository_quoted (self, r, a, b, ) :
        _re_repo = list(r.finditer(self._command, ), )

        _command = self._command
        for j in range(len(_re_repo) - 1, -1, -1, ) :
            i = _re_repo[j]
            _new_path = re.compile(
                "^(%s)" % (re.escape(a, ), ),
            ).sub(b, i.group(2), )

            _command = "%s%s%s" % (_command[:i.start(2)], _new_path, _command[i.end(2):], )

        return _command

    def replace_path (self, a, b, ) :
        if self._r is None :
            return self._command

        (_none, _r, ) = self.COMMANDS_HAS_REPOSITORY.get(self._r, )
        if _r == self.RE_REPOSITORY_WITH_LEN :
            _method = self._replace_path_with_len
        elif _r == self.RE_REPOSITORY_QUOTED :
            _method = self._replace_path_quoted
        else :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

        return _method(_r, a, b, )

    def _replace_path_with_len (self, r, a, b, ) :
        _re_repo = list(r.finditer(self._command, ), )

        _command = self._command
        for j in range(len(_re_repo) - 1, -1, -1, ) :
            i = _re_repo[j]
            _parsed = list(urlparse.urlsplit(i.group(2), ), )
            (a, b, _path, ) = map(utils.normpath, (a, b, _parsed[2], ), )

            _parsed[2] = utils.normpath(
                re.compile(
                    "^(%s)" % (re.escape(a), ),
                ).sub(b, _path, ),
            )

            _new_path = urlparse.urlunsplit(_parsed, )
            _command = "%s%s%s" % (_command[:i.start(1)], len(_new_path), _command[i.end(1):], )
            _command = "%s%s%s" % (_command[:i.start(2)], _new_path, _command[i.end(2):], )

        return _command

    def _replace_path_quoted (self, r, a, b, ) :
        _re_repo = list(r.finditer(self._command, ), )

        _command = self._command
        for j in range(len(_re_repo) - 1, -1, -1, ) :
            i = _re_repo[j]
            _parsed = list(urlparse.urlsplit(i.group(2), ), )
            (a, b, _path, ) = map(utils.normpath, (a, b, _parsed[2], ), )

            _parsed[2] = utils.normpath(
                re.compile(
                    "^(%s)" % (re.escape(a), ),
                ).sub(b, _path, ),
            )

            _new_path = urlparse.urlunsplit(_parsed, )
            _command = "%s%s%s" % (_command[:i.start(2)], _new_path, _command[i.end(2):], )

        return _command

    def get_repository_path (self, ) :
        (_none, _r, ) = self.COMMANDS_HAS_REPOSITORY.get(self._r, )
        _parsed = list(urlparse.urlsplit(_r.search(self._command, ).group(2), ), )
        return utils.normpath(_parsed[2], )

    def is_in (self, repos, ) :
        return bool(self.get_alias(repos, ))

    def get_alias (self, repos, ) :
        _path = self.get_repository_path() + "/"
        for i in repos :
            if re.compile("^%s\/" % re.escape(utils.normpath(i), ), ).search(_path, ) :
                return i

        return None


if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




