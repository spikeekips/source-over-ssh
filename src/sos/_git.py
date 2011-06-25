# -*- coding: utf-8 -*-


import re
import shlex

from twisted.internet import defer

import _base
import ssh_factory
import utils


class SessionTunnel (_base.BaseSessionTunnel, ) :
    name = "git"

    def parse_exec (self, ) :
        _parsed = shlex.split(self._commandline, )
        self._alias = _parsed[1]
        _available_repos = self._config_db.get_user_property(
                self._avatar.username, "repository", list(), )

        if not self._avatar._is_admin and self._alias not in _available_repos :
            utils.debug("not allowed this repository, `%s` to user, '%s'" % (
                self._alias, self.username, ), )
            self._session.loseConnection()

        _path = self._config_db.get_repository_property(self._alias, "path", )

        self._is_remote = self._config_db.is_remote_repository(self._alias, )
        if not self._is_remote :
            return "%s '%s'" % (_parsed[0], _path, )

        _r_parsed = self._config_db.parse_remote_repository(
                self._alias, )

        def _cb_open_session (r, ) :
            self._client.dataReceived = self._session.write
            self._client.extReceived = self._session.writeExtended

            self._client.open_session(
                "%s '%s'" % (
                    _parsed[0],
                    _r_parsed.get("path"),
                ),
            )
            return None

        self._client = ssh_factory.SSHClient(
            self._session,
            _r_parsed.get("host"),
            _r_parsed.get("port", ),
            _r_parsed.get("user"),
            self._config_db.get_repository_property(self._alias, "password", None, ),
        )
        return self._client.connect().addCallback(_cb_open_session, )

    def to_server (self, data, ) :
        _d = defer.maybeDeferred(super(SessionTunnel, self, ).to_server, data, )
        if self._client :
            _d.addCallback(self._client.write, )

        return _d

    RE_MSG_FATAL_NO_REPOSITORY = re.compile("fatal: '(.*)' does not appear to be a git repository", re.I, )

    def parse_to_client_extended (self, data, ) :
        _r = self.RE_MSG_FATAL_NO_REPOSITORY.search(data, )
        if _r :
            return data[:_r.start(1)] + self._alias + data[_r.end(1):]

        return data



