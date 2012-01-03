#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pwd
import resource
import sys

from twisted.application import service, strports
from twisted.cred.portal import Portal
from twisted.conch.ssh.keys import Key
from twisted.python import usage
from twisted.scripts import _twistd_unix

from config_db import ConfigDatabase
import ssh_factory
import utils


class ServerOptions (_twistd_unix.ServerOptions, ) :
    synopsis = "Usage: %s [options]" % sys.argv[0]

    longdesc = ""
    optFlags = [
        ["vv", None, "verbose", ],
        ["test", None, "run doctest", ],
        ["global", None, "allow global permission to every member", ],
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
            _h = pwd.getpwuid(os.geteuid(), ).pw_dir
            _d_sos = os.path.join(_h, ".sos")
            if not os.path.exists(_d_sos) :
                os.makedirs(_d_sos, )

            _f_cfg = os.path.join(_d_sos, "sos.cfg", )
            if not os.path.exists(_f_cfg, ) :
                if not os.path.exists(_f_cfg_default) :
                    raise usage.UsageError("can not find the default `sos.cfg`.", )

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

    if not _options.get("verbose") :
        utils.debug = lambda x : None

    resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024, ), )

    _open_key = lambda x : open(os.path.join(_options.get("host-key"), x, ), )
    _read_key = lambda x : Key.fromString(data=_open_key(x).read(), )

    factory = ssh_factory.SOSFactory()
    factory.privateKeys = {"ssh-rsa": _read_key("ssh_host_key"), }
    factory.publicKeys = {"ssh-rsa": _read_key("ssh_host_key.pub"), }

    _config_db = ConfigDatabase.from_filename(_options.get("config"), _global=_options.get("global"), )
    factory.portal = Portal(
        ssh_factory.SOSRealm(_config_db, verbose=_options.get("verbose"), ),
        (
            ssh_factory.SOSPublicKeyDatabase(_config_db, ),
            ssh_factory.ConfigDBPassword(_config_db, ),
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



