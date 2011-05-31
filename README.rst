##################################################
source+over+ssh
##################################################

`source+over+ssh` (aka, `sos`) manages the multiple source repositories over `ssh`
with *virtual* user account. it supports `svn`, `git` without any further
configuration of your client and also provide the management shell through
`ssh`.


feature
##################################################

 - virtual user (not actual system account)
 - alias path for the real repository path
 - passphrase and public key ssh authentication
 - `svn` and `git` support


install
##################################################

use `pip` (**not yet supported**)
==================================================

using `pip`, just search `sos` and install it. ::

    sh $ pip install source-over-ssh


from source
==================================================

requirement
--------------------------------------------------

 - `Python` 2.6 or higher <http://python.org>
 - `Twisted Network Framework` 11.0 or higher <http://twistedmatrix.com>

`sos` is written in `Python` and depends on the `Twisted Network Framework`,
especially `twisted conch`, so to install the `sos` you need `Python` and
`Twisted Conch`. if you install `sos` thru `pip`, `pip` will install these
things automatically with `sos`, but if you install from source, you install
these manually. ::

    sh $ apt-get install python2.6 # or python2.7
    sh $ apt-get install python-twisted-conch

or, ::

    sh $ pip install Twisted


`setup.py`
--------------------------------------------------

#. download the latest version of `sos` from https://github.com/spikeekips/source-over-ssh
#. run the `setup.py`::

    sh $ tar xf source-over-ssh-vX.X.X.tar.gz
    sh $ cd source-over-ssh-vX.X.X
    sh $ python -V
    sh $ python setup.py install

everything done.


generate ssh host key
==================================================

to run, you need ssh host key for `sso`. you can set the directory of host
key(private and public) manually by ``--host-key`` option, but if you run this
server within normal user, not `root`, i recommend you use your own ssh host
key. the default path is ``$HOME/.sos``. you can generate ssh host key like this,

::

    sh $ cd # cd $HOME
    sh $ mkdir .sos
    sh $ ssh-keygen -q -f .sos/ssh_host_key -N "" -t rsa

this command will generate two ssh host key files, ``ssh_host_key`` and
``ssh_host_key.pub`` without passpharase, these keys will be used only for `sso`.
`sso` will use this keys by default.


deploy
##################################################

after installation finished and the host keys are prepared, it's ready to deply
the `sos`. the deploy script are located at ``/bin`` from the installation root
path ::

    sh $ python setup.py install --prefix=/opt/sos

this command will install `sos` to the ``/opt/sos``. if you install without
``prefix``, the deploy script will be at the system default location, ``/usr/bin``.

you can run the deploy script like this, ::

    sh $ /opt/sos/bin/run_sos.py

this will launch the `sos` in background, as daemon. you can set these kind of
options manually, ::

    sh $ /opt/sos/run_sos.py --help

    Usage: /opt/sos/bin/run_sos.py [options]
    Options:
      -n, --nodaemon       don't daemonize, don't use default umask of 0077
          --syslog         Log to syslog, not to file
          --vv             verbose
      -l, --logfile=       log to a specified file, - for stdout
      -p, --profile=       Run in profile mode, dumping results to specified
                            file
          --profiler=      Name of the profiler to use (profile, cprofile,
                            hotshot). [default: hotshot]
          --prefix=        use the given prefix when syslogging [default: sso]
          --pidfile=       Name of the pidfile
          --host-key=      directory to look for host keys in`.
                            [default: $HOME/.sos]
          --config=        config file`. [default: $HOME/.sos/sos.cfg]
          --port=          ssh server port` [default: 2022]
          --interface=     network interface`
          --help-reactors  Display a list of possibly available reactor names.
          --version        Print version information and exit.
          --spew           Print an insanely verbose log of everything that
                            happens.  Useful when debugging freezes or locks in
                            complex code.
      -b, --debug          Run the application in the Python Debugger (implies
                            nodaemon), sending SIGUSR2 will drop into debugger
          --reactor=
          --help           Display this help and exit.

usually you will need these kind of options, ::

    sh $ /opt/sos/bin/run_sos.py --config=/etc/sos.cfg --port=2020 -n

this will use the custom config file, ``/etc/sos.cfg``, set the custom port, 2020
and run it without daemonizing.

.. note ::
    the `sos` will store the all the user account and source repository data
    into the config file. the default config file will be created automatically
    at the `.sos/sos.cfg` in your home directory.


get started
##################################################

access to the management shell
==================================================

without option, `sos` will use the ``2022`` port, you can access to the management
shell.

after clean installation, `sos` is prepared the one user, `admin`, this user can
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

the default `admin` password is `admin`. you must change the password after
first login.

change password
==================================================

::

    sos: admin $ password <new password>


add virtual user
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

    sso: spikeekips $

you can set your email and realname, and also change your password too.

.. note ::
   the email and realname will be used for svn, when you commit to the svn
   repository, this email and realname will be used as your identity.


add source repository
==================================================

::

    sos: admin $ admin repo add /home/spikeekips/workspace/sos/test/trunk /sos-trunk test repository
    repository, '/workspace/sos/test/trunk', alias, '/sos-trunk' was added.
    ===========================================================
     /workspace/sos/test/trunk   /sos-trunk (test repository)
    ===========================================================


the basic usage of adding repository is, ::

    sso: admin $ help admin repo add

    usage:
    admin repo add : $ admin repo add <repo path> [<alias>] [<description>]

``<repo path>`` is the real reposiotry path in your system, and
``<alias>`` is the shortcut or alias and you can access to the repository with
this alias, using alias you can access to your long repository name with alias.
without ``<alias>`` the alias name will be the same name of ``<repo path>``

::

    sh $ svn co svn+ssh://localhost/sos-trunk

this will access to the real repository, ``/workspace/sos/test/trunk``, so ``alias``
is the virtual path.


allow source repository to the user
==================================================

to access to the repository by the normal user, you can allow the registered
repository to the user. ::

    sso: admin $ admin repo allow user spikeekips /sos-test
    repository, '/sos-trunk' allowed to user, 'spikeekips'

you can also disallow the user, ::

    sso: admin $ admin repo disallow user spikeekips /sos-test
    sso: admin $ admin repo user list /sos-test
    ============================================================
     no users
    ============================================================
    (* is `admin`)


store public key for authentication without passpharase
==========================================================

you can login with your ssh public key without passpharase same as decent ssh
client. you store your ssh public key(not private key) to the `sso`.

.. note ::
    if you are not familiar with ssh or creating ssh public key, see this page,
    http://www.cs.wustl.edu/~mdeters/how-to/ssh/ .

open your ssh public key, which is usually ``.ssh/id_rsa.pub`` in your home
directory, and paste it. this is my personal public key ::

    sso: admin $ public_key view

    sso: admin $ public_key save ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAxbgqxA6IQO8
    ieZEGQAyZuOCe+ds7LSbjjCnUBzFAyVLJZKlxv+t1JdY+iLi/x/Q3tBHccr7Ueiy+I38AouwOUn8
    1UiViAU6IquNFlOMYMB/IoS5tVYEbHxoYpsZTUi/CuRNOLDfKG0avAXDSdQ9mp2ln1Ovv3pHQLeU
    uWni5ecslVC36vxpL49eLxr6uXaMnhDyyl9PbMnoudMeiyyyZVNIKK+QEonPLkxgYPk9l1baAtEA
    ph/zDsOwHfwo0DYgt8cPwyO6nzI9BoifVYWavCQoRsGtotf4AktTfL2AArJQc9jLLlzYsPwXK8g2
    QTLCHm7FED+Wm3T42Tsmn31eYGw== spikeekips@gmail.com


.. warning ::
    the upper public key was edited with new line for the example. the string
    of public key are very long, but you must enter your key **without any new
    line**.

and then, just try to connect, ::

    sh $ ssh -p2022 admin@localhost
    Enter passphrase for key '/home/spikeekips/.ssh/id_rsa':
    ...
    sso: admin $

.. note ::
    to skip asking passphrase for key, see this page,
    http://pkeck.myweb.uga.edu/ssh/


access your repository
##################################################

after adding repository and allowing user, you are ready to use your source
repository.

.. note ::
    when you run `sso` as non-root user, you wil not use the default ssh port,
    22. in this case, there are some problems with `svn`, using command line svn
    client you can not set the different port other than 22 directly, so you
    need some tip, adding the followings to the ``.ssh/config`` file from your
    home directory ::

        host <server hostname or ip address>
            Hostname <server hostname or ip address>
            Port 2022

::

    sh $ svn co svn+ssh://spikeekips@localhost/sso-test sso-test
    spikeekips@localhost's password: 
    A    test/..........
    ....................
    Checked out revision 20.
    Killed by signal 15.
    sh $
    
todo
##################################################

 * mirroring remote repository

get help
##################################################

 * GitHub https://github.com/spikeekips/source-over-ssh/issues.

