##################################################
source+over+ssh
##################################################

`source+over+ssh` (aka, `sos`) manages the multiple source repositories over `ssh`
with *virtual* user account. It supports `svn`, `git` without any further
configuration of your client and also provide the management shell through
`ssh`.

The one of the reason, why `source+over+ssh` was written was, that is. When you
serve the `svn` or `git` source repositories through ssh, you must create and
provide the actual system account (maybe that account be able to access to the
system shell, though you use ``git-shell``, it also can be the shell.). Using
`source+over+ssh` you don't need these kind of security problem. In the
`source+over+ssh`, there is no actual system account, every user is **virtual**.
You can protect your system from accidental security problems.


Feature
##################################################

 - **virtual user** (not actual system account)
 - alias path for the real repository path
 - passphrase and public key ssh authentication
 - `svn` and `git` support
 - **mirroring the remote repositories thru ssh**


Install
##################################################

`source+over+ssh` is written in `Python` and depends on the `Twisted Network
Framework`, especially `Twisted Conch`, so to install the `sos` you need
`Python` and `Twisted Conch`. If you install `sos` thru `pip`_, `pip` will
install these things automatically with `sos`, but if you install from source,
you install these manually.


Use `pip` (**not yet supported**)
==================================================

using `pip`, just search `source-over-ssh` and install it. ::

    sh $ pip install source-over-ssh


From Source
==================================================

Requirement
--------------------------------------------------

 - `Python` 2.6 or higher <http://python.org>
 - `Twisted Network Framework` 11.0 or higher <http://twistedmatrix.com>

if your system is debian or ubuntu, ::

    sh $ apt-get install python-twisted-conch python-crypto python-pyasn1

or, just use ``pip`` ::

    sh $ pip install Twisted pycrypto pyasn1


`setup.py`
--------------------------------------------------

#. Download the latest version of `sos` from https://github.com/spikeekips/source-over-ssh/downloads
#. Run the `setup.py`::

    sh $ tar xf source-over-ssh-vX.X.X.tar.gz
    sh $ cd source-over-ssh-vX.X.X
    sh $ python -V
    sh $ python setup.py install

Everything done.


Generate SSH Host Key
==================================================

To run, you need ssh host key for `sos`. You can set the directory of host
key(private and public) manually by ``--host-key`` option, but if you run this
server within normal user, not `root`, i recommend you use your own ssh host
key. The default path is ``$HOME/.sos``. You can generate ssh host key like this,

::

    sh $ cd # cd $HOME
    sh $ mkdir .sos
    sh $ ssh-keygen -q -f .sos/ssh_host_key -N "" -t rsa

This command will generate two ssh host key files, ``ssh_host_key`` and
``ssh_host_key.pub`` without passphrase, these keys will be used only for `sos`.
`sos` will use this keys by default.


Deploy
##################################################

After installation finished and the host keys are prepared, it's ready to deply
the `sos`. The deploy script are located at ``/bin`` from the installation root
path ::

    sh $ python setup.py install --prefix=/opt/sos

This command will install `sos` to the ``/opt/sos``. if you install without
``prefix``, the deploy script will be at the system default location, ``/usr/bin``.

You can run the deploy script like this, ::

    sh $ /opt/sos/bin/run_sos.py

This will launch the `sos` in background, as daemon. You can set these kind of
options manually, ::

    sh $ /opt/sos/run_sos.py --help

    Usage: /opt/sos/bin/run_sos.py [options]
    Options:
      -n, --nodaemon       don't daemonize, don't use default umask of 0077
          --syslog         Log to syslog, not to file
          --vv             verbose
      -l, --logfile=       log to a specified file, - for stdout
      -p, --profile=       Run in profile mode, dumping results to specified file
          --profiler=      Name of the profiler to use (profile, cprofile, hotshot). [default: hotshot]
          --prefix=        use the given prefix when syslogging [default: sos]
          --pidfile=       Name of the pidfile
          --host-key=      directory to look for host keys in`.  [default: $HOME/.sos]
          --config=        config file`. [default: $HOME/.sos/sos.cfg]
          --port=          ssh server port` [default: 2022]
          --interface=     network interface`
          --help-reactors  Display a list of possibly available reactor names.
          --version        Print version information and exit.
          --spew           Print an insanely verbose log of everything that happens.  Useful when debugging freezes or locks
                            in complex code.
      -b, --debug          Run the application in the Python Debugger (implies nodaemon), sending SIGUSR2 will drop into debugger
          --reactor=
          --help           Display this help and exit.

Usually you will need these kind of options, ::

    sh $ /opt/sos/bin/run_sos.py --config=/etc/sos.cfg --port=2020 -n

This will use the custom config file, ``/etc/sos.cfg``, set the custom port, 2020
and run it without daemonizing.

.. note ::
    The `sos` will store the all the user account and source repository data
    into the config file. the default config file will be created automatically
    at the `.sos/sos.cfg` in your home directory.


Get Started
##################################################

Access To The Management Shell
==================================================

Without option, `sos` will use the ``2022`` port, you can access to the management
shell.

After clean installation, `sos` is prepared the one user, `admin`, this user can
manage the server, like adding or removing user, repository, etc. ::

    sh $ ssh -p 2022 admin@localhost
    The authenticity of host '[localhost]:2022 ([127.0.0.1]:2022)' can't be established.
    RSA key fingerprint is xxxxxxxxxxxxxxxxxxxxxxxxxxx.
    Are you sure you want to continue connecting (yes/no)? yes
    Warning: Permanently added '[localhost]:2022' (RSA) to the list of known hosts.
    admin@localhost's password:
    Welcome to source+over+ssh server.

    usage:
    COMMANDS : 'public_key', 'realname', 'quit', 'admin', 'clear', 'repo', 'user', 'password', 'email', 'help'

    sos: admin $

The default `admin` password is `admin`. you must change the password after
first login.

Change Password
==================================================

::

    sos: admin $ password <new password>


Add Virtual User
==================================================

::

    sos: admin $ admin user add spikeekips my-password
    sos: admin $ quit

and access as new user, ``spikeekips``. ::

    sh $ ssh -p 2022 spikeekips@localhost
    spikeekips@localhost's password:
    Welcome to source+over+ssh server.

    usage:
    COMMANDS : 'public_key', 'realname', 'quit', 'clear', 'repo', 'user', 'password', 'email', 'help'

    sos: spikeekips $

You can set your email and realname, and also change your password too.

.. note ::
   The email and realname will be used for svn, when you commit to the svn
   repository, this email and realname will be used as your identity.


Add Source Repository
==================================================

::

    sos: admin $ admin repo add /home/spikeekips/workspace/sos/test/trunk /sos-trunk test repository
    repository, '/workspace/sos/test/trunk', alias, '/sos-trunk' was added.
    ======================================================================
     path                        alias                         is remote?
    =========================== ============================== ===========
     /workspace/sos/test/trunk   /sos-trunk (test repository)   O
    ======================================================================


The basic usage of adding repository is, ::

    sos: admin $ help admin repo add

    usage:
    admin repo add : $ admin repo add <repo path> [<alias>] [<description>]

``<repo path>`` is the real reposiotry path in your system, and
``<alias>`` is the shortcut or alias and you can access to the repository with
this alias, using alias you can access to your long repository name with alias.
Without ``<alias>`` the alias name will be the same name of ``<repo path>``

::

    sh $ svn co svn+ssh://localhost/sos-trunk

This will access to the real repository, ``/workspace/sos/test/trunk``, so ``alias``
is the virtual path.


Allow Source Repository To The User
==================================================

To access to the repository by the normal user, you can allow the registered
repository to the user. ::

    sos: admin $ admin repo allow user spikeekips /sos-test
    repository, '/sos-trunk' allowed to user, 'spikeekips'

You can also disallow the user, ::

    sos: admin $ admin repo disallow user spikeekips /sos-test
    sos: admin $ admin repo user list /sos-test
    ============================================================
     no users
    ============================================================


Store Public Key For Authentication Without Passphrase
==========================================================

You can login with your ssh public key without passphrase same as decent ssh
client. you store your ssh public key(not private key) to the `sos`.

.. note ::
    If you are not familiar with ssh or creating ssh public key, see this page,
    http://www.cs.wustl.edu/~mdeters/how-to/ssh/ .

Open your ssh public key, which is usually ``.ssh/id_rsa.pub`` in your home
directory, and paste it. this is my personal public key ::

    sos: admin $ public_key view

    sos: admin $ public_key save ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAxbgqxA6IQO8ieZEGQAyZuOCe+ds7LSbjjCnUBzFAyVLJZKlxv+t1JdY+
            iLi/x/Q3tBHccr7Ueiy+I38AouwOUn81UiViAU6IquNFlOMYMB/IoS5tVYEbHxoYpsZTUi/CuRNOLDfKG0avAXDSdQ9mp2ln1Ovv3pHQLeUuWni5e
            cslVC36vxpL49eLxr6uXaMnhDyyl9PbMnoudMeiyyyZVNIKK+QEonPLkxgYPk9l1baAtEAph/zDsOwHfwo0DYgt8cPwyO6nzI9BoifVYWavCQoRsG
            totf4AktTfL2AArJQc9jLLlzYsPwXK8g2QTLCHm7FED+Wm3T42Tsmn31eYGw== spikeekips@gmail.com


.. warning ::
    The upper public key was edited with new line for the example. The string
    of public key are very long, but you must enter your key **without any new
    line**.

And then, just try to connect, ::

    sh $ ssh -p2022 admin@localhost
    Enter passphrase for key '/home/spikeekips/.ssh/id_rsa':
    ...
    sos: admin $

.. note ::
    To skip asking passphrase for key, see this page,
    http://pkeck.myweb.uga.edu/ssh/


Access Your Repository
##################################################

After adding repository and allowing user, you are ready to use your source
repository.

.. note ::
    When you run `sos` as non-root user, you wil not use the default ssh port,
    22. In this case, there are some problems with `svn`, using command line svn
    client you can not set the different port other than 22 directly, so you
    need some tip, adding the followings to the ``.ssh/config`` file from your
    home directory ::

        host <server hostname or ip address>
            Hostname <server hostname or ip address>
            Port 2022

::

    sh $ svn co svn+ssh://spikeekips@localhost/sos-test sos-test
    spikeekips@localhost's password:
    A    test/..........
    ....................
    Checked out revision 20.
    Killed by signal 15.
    sh $


Add Remote Repository
##################################################

You can do mirroring the repositories in the another server, so you can provide
the one access point to access the repositories of various remote servers.

.. note ::
    At this time, `sos` just only support ssh connection to the remote server.

::

    sos: admin $ admin repo add remote <remote repo uri> <password> [<alias>] [<description>]
::

    sos: admin $ admin repo add remote svn+ssh://remoteuser@remote-server/svn-repository this-is-password /remote-svn
    remote repository, 'svn+ssh://remoteuser@remote-server/svn-repository', alias, '/remote-svn' was added.

    =====================================================================================
     path                                                 alias           is remote?
    ==================================================== =============== ================
     svn+ssh://remoteuser@remote-server/svn-repository    /remote-svn      O
    ---------------------------------------------------- --------------- ----------------
     ....
    =====================================================================================

You added successfully the repository of the remote server, `remote-server` and
the remote user `remoteuser` with `password`. After adding, you can check the
connectivity using `admin repo check` command,

::

    sos: admin $ admin repo check <alias>

::

    sos: admin $ admin repo check /remote-svn
    remote repository, '/remote-svn'('svn+ssh://remoteuser@remote-server/svn-repository') is accessible.

If the remote server is not valid, it will show the error messages.

To access this remote repository, follow the same way of local repository. ::

    sh $ svn co svn+ssh://localhost/remote-svn


TODO
##################################################

 * mirroring remote repository

Get Help
##################################################

 * GitHub https://github.com/spikeekips/source-over-ssh/issues .


