#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import shlex
import re
import string
import pwd
import resource
import urlparse
import base64
import binascii
import pty

from twisted.application import service, strports
from twisted.internet import defer, process
from twisted.internet.error import ProcessExitedAlready
from twisted.python import log, failure, usage
from twisted.scripts import _twistd_unix

from twisted.cred import credentials
from twisted.cred.portal import Portal
from twisted.cred.checkers import ICredentialsChecker

from twisted.conch import recvline, error
from twisted.conch.avatar import ConchUser
from twisted.conch.checkers import SSHPublicKeyDatabase
from twisted.conch.interfaces import ISession
from twisted.conch.insults import insults
from twisted.conch.ssh import session, transport
from twisted.conch.ssh.keys import Key
from twisted.conch.ssh.factory import SSHFactory
from twisted.conch.unix import UnixConchUser

from zope.interface import implements

import shell
import _exceptions
import utils
from config_db import ConfigDatabase


class SOSFactory (SSHFactory, ) :
    class protocol (transport.SSHServerTransport, ) :
        protocolVersion = "2.0"
        version = "OpenSSH_5.8p1"
        comment = "Debian-1ubuntu3"
        ourVersionString = ('SSH-' + protocolVersion +
                "-" + version + " " + comment).strip()


class SOSSession (session.SSHSession, ) :
    def __init__ (self, *a, **kw) :
        session.SSHSession.__init__(self, *a, **kw)

        self._request_type = None

    def request_subsystem (self, data, ) :
        log.msg("entering subsystem", )
        self._request_type = "subsystem"
        return session.SSHSession.request_subsystem(self, data, )

    def request_shell (self, data, ) :
        log.msg("entering shell", )
        self._request_type = "shell"
        return session.SSHSession.request_shell(self, data, )

    def request_pty_req (self, data, ) :
        log.msg("entering pty_req", )
        self._request_type = "pty_req"
        return session.SSHSession.request_pty_req(self, data, )

    def request_exec (self, data, ) :
        log.msg("entering exec", )
        self._request_type = "exec"
        return session.SSHSession.request_exec(self, data, )

    _buf = str()

    def dataReceived (self, data, ) :
        if self._request_type not in ("shell", ) :
            log.msg("data received: %s: %s" % (
                self._request_type, [data, ], ), )
        else :
            if data == "\r" :
                if self._buf :
                    log.msg("data received: %s: %s" % (
                        self._request_type, [(self._buf + data), ], ), )
                self._buf = str()
            else :
                self._buf += data

        return session.SSHSession.dataReceived(self, data, )


class SOSProtocol (recvline.HistoricRecvLine, ) :
    TERMINAL_COLOR_SUPPORTED = ("xterm", "xterm-color", "linux", )

    def __init__(self, avatar, config_db, ) :
        self._avatar = avatar
        self._config_db = config_db

        self._is_admin = self._config_db.is_admin(self._avatar.username, )
        self._is_xterm = self._avatar._env.get("TERM", "xterm",
                ) in self.TERMINAL_COLOR_SUPPORTED

        _ms = filter(lambda f: f.startswith('command_'), dir(self))
        self._commands = [c.replace('command_', '', 1) for c in _ms]

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
            log.msg("avatar: data received: %s" % ([line, ], ), )

        line = line.strip()
        if not line :
            self.showPrompt()
            return

        _sc = shell.ShellCommand(
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
        _sc = shell.ShellCommand(
            self._avatar.username,
            self._config_db,
            is_xterm=self._is_xterm,
            window_size=self._avatar._window_size[:2],
        )
        for i in _sc.run("help", ) :
            self.write(i, )


class SOSAvatar (ConchUser, ) :
    implements(ISession)

    RE_SHELL_ENVS = re.compile("^\w+\=.*$")

    def __init__ (self, username, config_db, verbose=False, ) :
        ConchUser.__init__(self)

        self._verbose = verbose
        self._config_db = config_db

        self._system_user = UnixConchUser(pwd.getpwuid(os.geteuid()).pw_name, )

        self._is_admin = self._config_db.is_admin(username, )

        self.username = username
        self.channelLookup.update({'session': SOSSession, })

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
            except (OSError, ProcessExitedAlready, ) :
                pass

            self._pty.loseConnection()

        log.msg("shell closed", )

    def windowChanged (self, window_size, ) :
        self._window_size = window_size

    allowed_commands = {
        "git-receive-pack": "git_receive_pack",
        "git-upload-pack": "git_upload_pack",
        "svnserve": "svnserve",
    }

    def check_git_repository_permission (self, command, ) :
        _parsed = shlex.split(command, )
        _repo = _parsed[1]
        _available_repos = self._config_db.get_user_property(
                self.username, "repository", list(), )

        if _repo not in _available_repos :
            log.msg("not allowed this repository, `%s` to user, '%s'" % (
                _repo, self.username, ), )
            raise _exceptions.PERMISSION_DENIED

        return (_parsed, self._config_db.get_repository_property(
            _repo, "path", ), )

    def execCommand (self, protocol, command, ) :
        _parsed = shlex.split(command, )
        if _parsed[0] not in self.allowed_commands :
            log.msg("not allowed this command, `%s`" % command, )
            self.conn.transport.loseConnection()

        _name = self.allowed_commands.get(_parsed[0], -1, )
        if _name == -1 :
            _name = "run_in_shell"

        return getattr(self, "_exec_%s" % _name, )(protocol, command, )

    def _exec_git_upload_pack (self, protocol, command, ) :
        try :
            (_parsed, _path, ) = self.check_git_repository_permission(command)
        except _exceptions.PERMISSION_DENIED :
            self.conn.transport.loseConnection()
            return

        return self._exec_run_in_shell(protocol, "%s %s" % (
            _parsed[0], _path, ), )

    def _exec_git_receive_pack (self, protocol, command, ) :
        try :
            (_parsed, _path, ) = self.check_git_repository_permission(command)
        except _exceptions.PERMISSION_DENIED :
            self.conn.transport.loseConnection()
            return

        return self._exec_run_in_shell(protocol, "%s %s" % (
            _parsed[0], _path, ), )

    def _exec_svnserve (self, protocol, command, ) :
        _parsed = shlex.split(command, )

        # split commands and environment variables
        _argvs = list()
        _envs = dict()
        _skip_envs = False
        for i in _parsed :
            if not _skip_envs and self.RE_SHELL_ENVS.match(i) :
                _envs.update((i.split("="), ), )
                continue

            if not _skip_envs :
                _skip_envs = True

            if i.startswith("--tunnel-user=") :
                continue
            _argvs.append(i, )

        if not _argvs :
            log.debug("invalid command, %s" % command, )
            self.conn.transport.loseConnection()

        _argvs.append("--tunnel-user='%s'" % (
            self._config_db.get_full_username(self.username, ), ),
        )

        from twisted.internet import reactor
        _shell = self._system_user.getShell()
        _process = SVNProcess(
            reactor,
            _shell,
            (_shell, "-c", command, ),
            self._env,
            "/tmp/",  # path
            protocol,  # protocol
            None,  # uid
            None,  # gid
            None,  # usePTY
            avatar=self,
        )

        return self._exec_run_in_shell(
                protocol, " ".join(_argvs), process_object=_process, )

    def _exec_run_in_shell (self, protocol, command, process_object=None, ) :
        #peer = self.conn.transport.transport.getPeer()
        #host = self.conn.transport.transport.getHost()
        #self._env['SSH_CLIENT'] = '%s %s %s' % (peer.host, peer.port, host.port, )

        try :
            if process_object is not None :
                self._pty = process_object
            else :
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

    def getPty (self, term, window_size, modes, ) :
        self._env["TERM"] = term
        self._window_size = window_size
        self._modes = modes

        _master, _slave = pty.openpty()
        _ttyname = os.ttyname(_slave)
        self._env["SSH_TTY"] = _ttyname
        self.ptyTuple = (_master, _slave, _ttyname, )

    def openShell (self, protocol, ) :
        serverProtocol = insults.ServerProtocol(
                SOSProtocol, self, self._config_db, )
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


class SOSPublicKeyDatabase (SSHPublicKeyDatabase, ) :
    def __init__ (self, config_db, ) :
        self._config_db = config_db

    def checkKey (self, credentials, ) :
        if not self._config_db.has_user(credentials.username, ) :
            return False

        _public_key = self._config_db.get_user_property(
            credentials.username, "public_key", )

        if not _public_key :
            return False

        try :
            return base64.decodestring(
                    _public_key.split()[1], ) == credentials.blob
        except (binascii.Error, IndexError, ) :
            pass

        return False


class ConfigDBPassword (object, ) :
    implements(ICredentialsChecker)
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


class SVNProcessParser (object, ) :
    def restore (self, data, ) :
        if self.proc._repo_alias is None or self.proc._repo_real is None :
            return data

        try :
            _sh = SVNCommandParser(data, )
        except (ValueError, IndexError,
                _exceptions.BAD_SVN_REPOSITORY_COMMAND, ) :
            return data

        return _sh.replace_path(self.proc._repo_real, self.proc._repo_alias, )

    def convert (self, data, ) :
        try :
            _sh = SVNCommandParser(data, )
        except (_exceptions.BAD_SVN_REPOSITORY_COMMAND,
                ValueError, IndexError, ) :
            return data

        _available_repos = self.proc._avatar._config_db.get_user_property(
            self.proc._avatar.username, "repository", list(), )

        _alias = _sh.get_alias(_available_repos, )
        if not _alias :
            _msg = "not allowed this repository, `%s` to user, '%s'" % (
                _sh.get_repository_path(),
                self.proc._avatar.username,
            )
            log.msg(_msg, )
            raise ProcessExitedAlready(_msg, )

        self.proc._repo_alias = _alias
        self.proc._repo_real = self.proc._avatar._config_db.get_repository_property(
            self.proc._repo_alias, "path", )

        return _sh.replace_path(self.proc._repo_alias, self.proc._repo_real, )


class SVNProcessReader (process.ProcessReader, SVNProcessParser, ) :
    def dataReceived (self, data, ) :
        _data = self.restore(data)
        if self.proc._avatar._verbose :
            log.msg(">> reader: ", [data, ], )
            log.msg("<< reader: ", [_data, ], )

        return process.ProcessReader.dataReceived(self, _data, )


class SVNProcessWriter (process.ProcessWriter, SVNProcessParser, ) :
    def write (self, data, ) :
        try :
            _data = self.convert(data)
        except ProcessExitedAlready :
            self.proc._avatar.conn.transport.loseConnection()
            return

        if self.proc._avatar._verbose :
            log.msg(">> writer: ", [data, ], )
            log.msg("<< writer: ", [_data, ], )

        return process.ProcessWriter.write(self, _data, )


class SVNProcess (process.Process, ) :
    processReaderFactory = SVNProcessReader
    processWriterFactory = SVNProcessWriter

    def __init__ (self, *a, **kw) :
        self._avatar = kw.get("avatar")
        if "avatar" in kw :
            del kw["avatar"]

        process.Process.__init__(self, *a, **kw)

        self._repo_alias = None
        self._repo_real = None


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


class ServerOptions (_twistd_unix.ServerOptions, ) :
    synopsis = "Usage: %s [options]" % sys.argv[0]

    longdesc = ""
    optFlags = [
        ["vv", None, "verbose", ],
        ["test", None, "run doctest", ],
    ]

    optParameters = [
        ["host-key", None, None, "directory to look for host keys in`. [default: $HOME/.sos]", ],
        ["config", None, None, "config file`. [default: $HOME/.sos/sos.cfg]", ],
        ["port", None, 2022, "ssh server port`", ],
        ["interface", None, None, "network interface`", ],
        ["pidfile", None, None, "Name of the pidfile", ],
        ["prefix", None, "sso", "use the given prefix when syslogging", ],
    ]

    unused_long = ("--chroot=", "--euid", "--umask=", "--rundir=", "--python=", "--savestats", "--no_save",
        "--encrypted", "--file=", "--source=", "--uid=", "--gid=", "--test", "--originalname", )
    remove_key = ("--euid", "--uid=", "--gid=", )
    unused_short = ("-o", "-f", "-s", "-y", "-d", "-g", "-u", )

    def __init__ (self, *a, **kw) :
        _twistd_unix.ServerOptions.__init__(self, *a, **kw)

        for i in self.unused_long :
            if self.longOpt.count(i[2:]) > 0 :
                del self.longOpt[self.longOpt.index(i[2:])]

    def __getattribute__ (self, k, ) :
        if k == "subCommands" :
            raise AttributeError

        return _twistd_unix.ServerOptions.__getattribute__(self, k, )

    def parseOptions (self, *a, **kw) :
        self._skip_reactor = kw.get("skip_reactor")
        if "skip_reactor" in kw :
            del kw["skip_reactor"]

        super(ServerOptions, self).parseOptions(*a, **kw)

    def opt_vv (self, value, ) :
        del self["vv"]
        self["verbose"] = True

    def opt_port (self, value, ) :
        try :
            self["port"] = int(value, )
        except :
            raise usage.UsageError("invalid port number.", )

    def opt_reactor (self, v, ) :
        if self._skip_reactor :
            return
        return _twistd_unix.ServerOptions.opt_reactor(self, v, )

    def postOptions (self, ) :
        _twistd_unix.ServerOptions.postOptions(self, )

        for i in map(lambda x : x[2:x.endswith("=") and -1 or None], self.remove_key, ) :
            if i in self :
                del self[i]

        self["uid"] = None
        self["gid"] = None
        self["euid"] = True

        if not self.get("nodaemon") :
            if not self.get("pidfile") :
                self["pidfile"] = "/tmp/sos-%d.pid" % self.get("port")

            if not self.get("logfile") :
                self["logfile"] = "/tmp/sos-%d.log" % self.get("port")

        #if not self.get("config") :
        #    raise usage.UsageError("config file must be given", )
        if self.get("config") and not os.path.exists(self.get("config")) :
            raise usage.UsageError("config file, '%s' does not exist" % self.get("config"), )

        if not self._skip_reactor :
            # create default environment in $HOME/.sos
            _f_cfg_default = os.path.join(
                os.path.dirname(__file__),
                "data",
                "sos.cfg",
            )
            if not os.path.exists(_f_cfg_default) :
                log.msg("can not find the default `sos.cfg`.")
                return

            _h = pwd.getpwuid(os.geteuid(), ).pw_dir
            _d_sos = os.path.join(_h, ".sos")
            if not os.path.exists(_d_sos) :
                os.makedirs(_d_sos, )

            _f_cfg = os.path.join(_d_sos, "sos.cfg", )
            if not os.path.exists(_f_cfg, ) :
                with file(_f_cfg, "w") as f :
                    f.write(file(_f_cfg_default).read(), )

            if not self.get("config") :
                sys.argv.append("--config=%s" % _f_cfg, )

            # check the host key
            _keypath = self.get("host-key")
            if _keypath :
                if not os.path.exists(_keypath, ) :
                    raise usage.UsageError("the directory for host key does not exist. '%s'" % _keypath, )
            else :
                _keypath = _d_sos

            if not filter(
                        lambda x : os.path.exists(os.path.join(_keypath, x), ),
                        ("ssh_host_key", "ssh_host_key.pub", ),
                    ) :
                _description = """can not find the host keys, 'ssh_host_key', 'ssh_host_key.pub' in '%s'.

you can set the host key path using `--host-key=<path>`, or you can generate your own ssh host key like this,

sh $ ssh-keygen -q -f %s/ssh_host_key -N "" -t rsa

and re-run this script.

"""
                raise usage.UsageError(_description % (_keypath, _keypath, ), )

            sys.argv.append("--host-key=%s" % _keypath, )


def run_application () :
    _options = ServerOptions()
    _options.parseOptions(skip_reactor=True, )

    if _options.get("test") :
        import doctest
        doctest.testmod()
        sys.exit()

    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024, ), )

    _open_key = lambda x : open(os.path.join(_options.get("host-key"), x, ), )
    with _open_key("ssh_host_key") as privateBlobFile:
        privateBlob = privateBlobFile.read()
        private_key = Key.fromString(data=privateBlob, passphrase="abu333spike", )

    with _open_key("ssh_host_key.pub") as publicBlobFile:
        publicBlob = publicBlobFile.read()
        public_key = Key.fromString(data=publicBlob, )

    factory = SOSFactory()
    factory.privateKeys = {"ssh-rsa": private_key, }
    factory.publicKeys = {"ssh-rsa": public_key, }

    _config_db = ConfigDatabase.from_filename(_options.get("config"), )
    factory.portal = Portal(
        SOSRealm(_config_db, verbose=_options.get("verbose"), ),
        (
            SOSPublicKeyDatabase(_config_db, ),
            ConfigDBPassword(_config_db, ),
        ),
    )

    application = service.Application("source+over+ssh server", )
    strports.service(
        "tcp:%d%s" % (
            _options.get("port"),
            _options.get("interface") and (":interface=%s" % _options.get("interface")) or "",
        ),
        factory,
    ).setServiceParent(application, )

    return application


def run_script (_f) :
    _found = False
    _n = list()
    _n.append(sys.argv[0], )
    for i in sys.argv[1:] :
        if _found :
            _found = False
            continue
        elif i in ServerOptions.unused_short :
            _found = True
            continue
        elif filter(i.startswith, ServerOptions.unused_long, ) :
            continue

        _n.append(i, )

    _n.extend(["-y", _f, ], )
    sys.argv = _n

    from twisted.application import app
    from twisted.scripts.twistd import runApp
    app.run(runApp , ServerOptions, )



