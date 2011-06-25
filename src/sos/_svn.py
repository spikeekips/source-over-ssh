# -*- coding: utf-8 -*-


import re
import shlex
import string
import urlparse

from twisted.internet import defer

import _base
import _exceptions
import ssh_factory
import utils


class SessionTunnel (_base.BaseSessionTunnel, ) :
    name = "svn"

    _buf = list()

    def __init__ (self, *a, **kw) :
        super(SessionTunnel, self).__init__(*a, **kw)

        self._commandline_fixed = self._commandline
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

        self._commandline_fixed = " ".join(_argv, )
        return self._commandline_fixed

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
                    self._client.dataReceived = self._session.write

                    self._client.extReceived = self._session.writeExtended
                    self._client.open_session(self._commandline_fixed, )
                    return None

                self._client = ssh_factory.SSHClient(
                    self._session,
                    _parsed.get("host"),
                    _parsed.get("port", ),
                    _parsed.get("user"),
                    self._config_db.get_repository_property(self._alias, "password", None, ),
                )
                self._buf.append(self.replace_path_to_server(_cp, ), )
                return self._client.connect().addCallback(_cb_open_session, )

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
    RE_REPOSITORY = re.compile("([ \:\'\"\)\(])(svn\+ssh\:\/\/[\w%s]+)([ \'\"\)\(])" % _strings, re.I, )
    RE_LEN = re.compile("[\s]*([\d][\d]*)\:[^ ]", )

    _COMMANDS_HAS_REPOSITORY = {
        "edit-pipeline": "^[\s]*\([\s]*\d+[\s]*\([\s]*(?P<type>edit-pipeline).*\)",
        "success": "^[\s]*\([\s]*(?P<type>success)[\s]*\(",
        "failure": "^[\s]*\([\s]*(?P<type>failure)[\s*]\(",
        "reparent": "^\([\s]*(?P<type>reparent)[\s]*\(",
        "open-root": "^[\s]*\([\s]*(?P<type>open-root)[\s]*\(",
        "add-dir": "^[\s]*\([\s]*(?P<type>add-dir)[\s]*\(",
    }  # just history.

    def __init__ (self, command, ) :
        self._command = command

        if not self.IS_SVN_COMMAND.match(self._command, ) :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

        if not self.RE_REPOSITORY.search(self._command, ) or not self.RE_LEN.search(self._command, ) :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

    def get_client_base (self, alias, ) :
        _command = "".join(self._command, )
        _alias = utils.normpath(alias, )
        _base = None

        _r_repo = list(self.RE_REPOSITORY.finditer(_command, ))
        for i in xrange(len(_r_repo, ) - 1, -1, -1, ) :
            j = _r_repo[i]

            _parsed = list(urlparse.urlsplit(j.group(2), ), )
            _parsed[2] = _alias
            _base = urlparse.urlunsplit(_parsed, )

            break

        if _base is None :
            raise _exceptions.BAD_SVN_REPOSITORY_COMMAND

        return _base

    def get_repository_path (self, ) :
        _command = "".join(self._command, )

        _r_repo = list(self.RE_REPOSITORY.finditer(_command, ))
        for i in xrange(len(_r_repo, ) - 1, -1, -1, ) :
            j = _r_repo[i]

            _parsed = list(urlparse.urlsplit(j.group(2), ), )
            return utils.normpath(_parsed[2], )

    def is_in (self, repos, ) :
        return bool(self.get_alias(repos, ))

    def get_alias (self, avalable_aliases, ) :
        _aliases = list(avalable_aliases)[:]
        _aliases.sort()
        _aliases.reverse()

        _path = self.get_repository_path()
        for i in _aliases :
            if re.compile("^%s" % re.escape(utils.normpath(i), ), ).search(_path, ) :
                return i

        return None

    def replace_path (self, a, b, ) :
        # clone from `http://rosettacode.org/wiki/Copy_a_string#Python`
        _command = "".join(self._command, )
        (a, b, ) = map(utils.normpath, (a, b, ), )

        _matches_len = list(self.RE_LEN.finditer(_command, ))
        _r_repo = list(self.RE_REPOSITORY.finditer(_command, ))

        for i in xrange(len(_r_repo, ) - 1, -1, -1, ) :
            j = _r_repo[i]
            _ml = filter(lambda x : x.start(1) < j.start(2), _matches_len, )[-1]

            _parsed = list(urlparse.urlsplit(j.group(2), ), )
            _parsed[2] = re.compile("^(%s)" % (re.escape(a), ), ).sub(
                b,
                utils.normpath(_parsed[2], ),
            )

            _new_path = urlparse.urlunsplit(_parsed, )

            _command = "%s%s%s" % (_command[:j.start(2)], _new_path, _command[j.end(2):], )
            _command = "%s%s%s" % (
                _command[:_ml.start(1)],
                int(_command[_ml.start(1):_ml.end(1)]) + (len(_new_path) - len(j.group(2))),
                _command[_ml.end(1):],
            )

        return _command

    def replace_repository (self, a, b, ) :
        _command = "".join(self._command, )

        _matches_len = list(self.RE_LEN.finditer(_command, ))
        _r_repo = list(self.RE_REPOSITORY.finditer(_command, ))

        for i in xrange(len(_r_repo, ) - 1, -1, -1, ) :
            j = _r_repo[i]
            _ml = filter(lambda x : x.start(1) < j.start(2), _matches_len, )[-1]

            _new_path = re.compile("^(%s)" % (re.escape(a), ), ).sub(b, j.group(2), )

            _command = "%s%s%s" % (_command[:j.start(2)], _new_path, _command[j.end(2):], )
            _command = "%s%s%s" % (
                _command[:_ml.start(1)],
                int(_command[_ml.start(1):_ml.end(1)]) + (len(_new_path) - len(j.group(2))),
                _command[_ml.end(1):],
            )

        return _command


if __name__ == "__main__"  :
    import doctest
    doctest.testmod()




