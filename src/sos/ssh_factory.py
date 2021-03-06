# -*- coding: utf-8 -*-


import base64
import binascii
import os
import pty
import pwd
import shlex

from twisted.cred import credentials, checkers as checkers_cred
from twisted.conch import error, unix, checkers as checkers_conch, avatar, interfaces as interfaces_conch
from twisted.conch.client import direct, knownhosts, options
from twisted.conch.insults import insults
from twisted.conch.ssh import (session, transport, common, channel, keys, userauth, connection,
        factory as ssh_factory, )
from twisted.internet import defer, error as error_internet
from twisted.python import failure, filepath

from zope.interface import implements

import _base
from config_db import ConfigDatabase
import _exceptions
import shell
import utils


ALLOWED_EXEC_COMMANDS = {
    "git-receive-pack": "git",
    "git-upload-pack": "git",
    "svnserve": "svn",
}


class SOSFactory (ssh_factory.SSHFactory, ) :
    class protocol (transport.SSHServerTransport, ) :
        protocolVersion = "2.0"
        version = "OpenSSH_5.8p1"
        comment = "Source+Over+SSH"
        ourVersionString = ("SSH-" + protocolVersion +
                "-" + version + " " + comment).strip()


class SOSSession (session.SSHSession, ) :
    def __init__ (self, *a, **kw) :
        session.SSHSession.__init__(self, *a, **kw)

        self._request_type = None
        self._session_tunnel = None

    def closed (self, ) :
        self._session_tunnel.close()
        del self._session_tunnel

        return session.SSHSession.closed(self, )

    def request_subsystem (self, data, ) :
        self.loseConnection()
        return

    def request_shell (self, data, ) :
        self._request_type = "shell"
        utils.debug("entering shell", )

        self._session_tunnel = _base.SessionTunnel(self, "", )

        return session.SSHSession.request_shell(self, data, )

    def request_pty_req (self, data, ) :
        self._request_type = "pty_req"
        utils.debug("entering pty_req", )
        return session.SSHSession.request_pty_req(self, data, )

    def request_exec (self, data, ) :
        self._request_type = "exec"

        (_c, _none, ) = common.getNS(data, )

        _n = shlex.split(_c, )[0]
        _command = _n in ALLOWED_EXEC_COMMANDS and ALLOWED_EXEC_COMMANDS.get(_n, ) or None

        if not _command :
            utils.debug("not allowed this command, `%s`" % str([data], ), )
            self.loseConnection()
            return

        self._session_tunnel = _base.get_session_tunnel(
                _command, _base.SessionTunnel, )(self, _c, )

        utils.debug("entering exec '%s'" % self._session_tunnel.name, )

        return defer.maybeDeferred(self._session_tunnel.get_exec, ).addCallback(self._cb_request_exec, )

    def _cb_request_exec (self, data, ) :
        if data is None :
            return True

        return session.SSHSession.request_exec(self, common.NS(data, ), )

    _buf = str()

    def dataReceived (self, data, ) :
        _msg = None
        if self._request_type not in ("shell", ) :
            _msg = data
        else :
            if not data.endswith("\r") :
                self._buf += data
            else :
                if self._buf :
                    _msg = self._buf + data

                self._buf = str()

        if _msg :
            utils.debug(">> received: %s: %s" % (self._request_type, [_msg, ], ), )

        return defer.maybeDeferred(self._session_tunnel.to_server, data,
                ).addCallbacks(
                    self._cb_to_server, self._eb_to_server,
                )

    def _cb_to_server (self, data, ) :
        if data is None :
            return

        if self._request_type not in ("shell", ) :
            utils.debug("<< write: %s: %s" % (
                self._request_type, [data, ], ), )

        return session.SSHSession.dataReceived(self, data, )

    def _eb_to_server (self, f, ) :
        if f.check(_exceptions.PERMISSION_DENIED, ) :
            self.loseConnection()

        return f.raiseException()

    def write (self, data, ) :
        return defer.maybeDeferred(self._session_tunnel.to_client, data,
                ).addCallbacks(self._cb_to_client, self._eb_to_client, )

    def writeExtended (self, data_type, data, ) :
        return defer.maybeDeferred(
                self._session_tunnel.to_client_extended, data,
            ).addCallback(
                self._cb_to_client_extended, data_type,
            ).addErrback(
                self._eb_to_client_extended,
            )

    def _cb_to_client_extended (self, data, data_type, ) :
        if data is None :
            return

        return session.SSHSession.writeExtended(self, data_type, data, )

    def _eb_to_client_extended (self, f, ) :
        f.raiseException()

    def _cb_to_client (self, data, ) :
        if data is None :
            return

        return session.SSHSession.write(self, data, )

    def _eb_to_client (self, f, ) :
        f.raiseException()


class SOSAvatar (avatar.ConchUser, ) :
    implements(interfaces_conch.ISession)

    def __init__ (self, username, config_db, verbose=False, ) :
        avatar.ConchUser.__init__(self)

        self.channelLookup.update({"session": SOSSession, })

        self._verbose = verbose
        self._config_db = config_db

        self._system_user = unix.UnixConchUser(pwd.getpwuid(os.geteuid()).pw_name, )

        self.username = username
        self._is_admin = config_db.is_admin(self.username, )

        self._pty = None
        self._env = dict(
            PATH="/bin:/usr/bin:/usr/local/bin",
        )

    def eofReceived (self, ) :
        if self._pty :
            self._pty.closeStdin()

    def closed (self, ) :
        if self._pty :
            try :
                self._pty.signalProcess("HUP")
            except (OSError, error_internet.ProcessExitedAlready, ) :
                pass

            self._pty.loseConnection()

        utils.debug("shell closed", )

    def windowChanged (self, window_size, ) :
        self._window_size = window_size

    def execCommand (self, protocol, command, ) :
        try :
            from twisted.internet import reactor
            _shell = self._system_user.getShell()
            self._pty = reactor.spawnProcess(
                protocol,
                _shell,
                args=(_shell, "-c", command, ),
                env=self._env,
                path="/tmp/",
                uid=None,
                gid=None,
                usePTY=False,
            )

            self.conn.transport.transport.setTcpNoDelay(1)
        except :
            if self._verbose :
                import traceback
                traceback.print_exc()

            self.conn.transport.loseConnection()

        return

    def getPty (self, term, window_size, modes, ) :
        self._env["TERM"] = term
        self._window_size = window_size
        self._modes = modes

        _master, _slave = pty.openpty()
        _ttyname = os.ttyname(_slave)
        self._env["SSH_TTY"] = _ttyname
        self.ptyTuple = (_master, _slave, _ttyname, )

    def openShell (self, protocol, ) :
        serverProtocol = insults.ServerProtocol(shell.SOSProtocol, self, )
        serverProtocol.makeConnection(protocol, )
        protocol.makeConnection(session.wrapProtocol(serverProtocol, ), )


class SOSRealm (object, ) :
    def __init__ (self, config_db, verbose=False, ) :
        self._config_db = config_db
        self._verbose = verbose

    def requestAvatar (self, avatarId, mind, *interfaces) :
        return (
            interfaces[0],
            SOSAvatar(avatarId, self._config_db, verbose=self._verbose, ),
            lambda : None,
        )


class SOSPublicKeyDatabase (checkers_conch.SSHPublicKeyDatabase, ) :
    def __init__ (self, config_db, ) :
        self._config_db = config_db

    def checkKey (self, credentials, ) :
        if not self._config_db.has_user(credentials.username, ) :
            return False

        _public_key = self._config_db.get_user_property(
            credentials.username, "public_key", )

        if not _public_key :
            return False

        #try :
        #    return base64.decodestring(
        #            _public_key.split()[1], ) == credentials.blob
        #except (binascii.Error, IndexError, ) :
        #    pass

        #return False

        try :
            return filter(lambda x : base64.decodestring(x.strip().split()[1], ) == credentials.blob, _public_key.split(','), )
        except (binascii.Error, IndexError, ) :
            import traceback
            traceback.print_exc()
        
        return False
        

class ConfigDBPassword (object, ) :
    implements(checkers_cred.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword, )

    def __init__ (self, config_db, ) :
        self._config_db = config_db

    def getUser (self, username, ) :
        if not self._config_db.has_user(username, ) :
            raise KeyError(username, )

        return (
                username,
                self._config_db.get_user_property(username, "password"),
        )

    def requestAvatarId (self, c, ) :
        try:
            u, p = self.getUser(c.username)
        except KeyError:
            return defer.fail(error.UnauthorizedLogin(), )
        else:
            if not p :
                return defer.fail(error.UnauthorizedLogin(), )

            return defer.maybeDeferred(
                lambda : ConfigDatabase.encrypt_password(c.password) == p,
            ).addCallback(self._cbPasswordMatch, u, )

    def _cbPasswordMatch (self, matched, username, ) :
        return matched and username or failure.Failure(
                error.UnauthorizedLogin())


##################################################
# ssh client
class SCSSHSession (channel.SSHChannel, ) :
    name = "session"

    def __init__ (self, *a, **kw) :
        kw.setdefault("command", None, )
        self._command = kw.get("command", None, )
        del kw["command"]

        channel.SSHChannel.__init__(self, *a, **kw)

    def channelOpen (self, *a, **kw) :
        utils.debug("session %s open" % self.id, )

        self.conn.sendRequest(self, "exec", common.NS(self._command, ), )

    def request_exit_status (self, data, ) :
        # TODO: send exit-status to the client.
        pass


class SCSSHConnection (connection.SSHConnection, ) :
    def __init__ (self, *a, **kw) :
        connection.SSHConnection.__init__(self, *a, **kw)

        self._client = None

    def get_session (self, ) :
        return self.channels.get(0, None, )

    def openChannel (self, client, command, extra="", ) :
        self._client = client
        return connection.SSHConnection.openChannel(
                self, SCSSHSession(command=command, ), extra, )

    def ssh_CHANNEL_OPEN_CONFIRMATION (self, *a, **kw) :
        connection.SSHConnection.ssh_CHANNEL_OPEN_CONFIRMATION(self, *a, **kw)

        self.get_session().dataReceived = self._client.dataReceived
        self.get_session().extReceived = self._client.extReceived
        self.write = self.get_session().write

    def serviceStarted (self, ) :
        utils.debug("ssh connection opened", )

    def channelClosed (self, channel, ) :
        utils.debug("connection closing %s" % channel, )
        utils.debug("stopping connection")

        if self._client :
            self._client.loseConnection()


class SSHUserAuthClient (userauth.SSHUserAuthClient, ) :
    def __init__ (self, user, password, *a, **kw) :
        userauth.SSHUserAuthClient.__init__(self, user, *a, **kw)
        self.getPassword = lambda *a, **kw : defer.succeed(password, )

        self._authed_password = False

        self.auth_public_key = lambda : False
        self.auth_keyboard_interactive = lambda : False

    def auth_password (self, ) :
        if self._authed_password :
            self.transport.factory.client.session.conn.transport.sendDisconnect(
                transport.DISCONNECT_NO_MORE_AUTH_METHODS_AVAILABLE,
                "Invalid password", )
            return False

        self._authed_password = True
        return userauth.SSHUserAuthClient.auth_password(self, )


class SSHClient (object, ) :
    def __init__ (self, session, host, port, user, password, ) :
        self.session = session

        self._options = options.ConchOptions()
        self._options.update(
            {
                "host": host,
                "port": port,
                "user": user,
                "compress": False,
                "notty": True,
                "known-hosts": os.path.expanduser("~/.sos/known_hosts"),
            }
        )
        self._password = password
        self.dataReceived = lambda x : x
        self.extReceived = lambda x : x

        self._tcp = None

    def _get_connection (self, ) :
        return self._tcp.factory.userAuthObject.instance

    def loseConnection (self, ) :
        self.session.loseConnection()

    def close (self, ) :
        if self._tcp :
            self._tcp.disconnect()

    @classmethod
    def verifyHostKey (cls, transport, ip, key_encoded, fingerprint, ) :
        hostname = transport.factory.options["host"]
        key = keys.Key.fromString(key_encoded, )
        kh = knownhosts.KnownHostsFile.fromPath(
            filepath.FilePath(transport.factory.options["known-hosts"], )
        )

        if kh.hasHostKey(hostname, key, ) :
            if not kh.hasHostKey(ip, key, ) :
                kh.addHostKey(ip, key, )
                kh.save()
        else :
            kh.addHostKey(hostname, key, )
            kh.addHostKey(ip, key, )
            kh.save()

        return defer.maybeDeferred(lambda : True, )

    def connect (self, ) :
        from twisted.internet import reactor
        self._tcp = reactor.connectTCP(
                self._options.get("host"),
                self._options.get("port"),
                direct.SSHClientFactory(
                    defer.Deferred(),
                    self._options,
                    self.__class__.verifyHostKey,
                    SSHUserAuthClient(
                        self._options.get("user"),
                        self._password,
                        SCSSHConnection(),
                    ),
                ),
            )

        self._tcp.factory.client = self

        return self._tcp.factory.d.addErrback(self._eb_connect, )

    def _eb_connect (self, f, ) :
        if f.check(error_internet.ConnectionRefusedError, ) :
            _ecode = transport.DISCONNECT_SERVICE_NOT_AVAILABLE
            _emsg = str(f.value, )
        else :
            _ecode = transport.DISCONNECT_CONNECTION_LOST
            _emsg = "problems occured."

        self.session.conn.transport.sendDisconnect(_ecode, _emsg, )
        self.session.loseConnection()

        return None

    def open_session (self, command, ) :
        return self._get_connection().openChannel(self, command, )

    def write (self, data, ) :
        # write to target
        utils.debug(">> to remote: " + str([data, ],))

        self._get_connection().write(data, )

