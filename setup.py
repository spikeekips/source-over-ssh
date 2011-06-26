# -*- coding: utf-8 -*-

import os

from distutils.core import setup
from distutils.command.build_py import build_py

long_description = """
`source-over-ssh` (source repository server over ssh) can manage the multiple
source repositories over `ssh` with virtual user account. It supports `svn`,
`git` and also provide the management shell through `ssh`.
"""


class SOSbuild_py (build_py, ) :
    def build_packages (self, *a, **kw) :
        build_py.build_packages(self, *a, **kw)

        _d = os.path.join(self.build_lib, self.packages[0], "data", )
        if not os.path.exists(_d) :
            os.makedirs(_d, )
        with file(os.path.join(_d, "sos.cfg", ), "w") as f :
            f.write(file("src/data/sos.cfg").read(), )

setup(
    cmdclass=dict(build_py=SOSbuild_py, ),
    name="source-over-ssh",
    version="0.3",
    description="source repository management server over ssh",
    long_description=long_description.replace("\n", " ").strip(),
    author="Spike^ekipS",
    author_email="spikeekips@gmail.com",
    url="https://github.com/spikeekips/source-over-ssh",
    download_url="https://github.com/spikeekips/source-over-ssh/downloads",
    platforms=["Any", ],
    license="GNU General Public License (GPL)",

    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Environment :: No Input/Output (Daemon)",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Topic :: Security",
        "Topic :: Software Development :: Version Control",
        "Topic :: System :: Systems Administration",
    ),

    packages=("sos", ),
    package_dir={"sos": "src/sos", },
    data_files=(
        ("etc", ("src/data/sos.cfg", ), ),
        ("bin", ("src/scripts/run_sos.py", ), ),
    ),

    install_requires=(
        "Twisted (>=11.0.0)",
        "pycrypto (>=3.2)",
        "pyasn1 (>=0.0.13b)",
    ),

)
