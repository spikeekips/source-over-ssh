#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__ == "__builtin__"  :
    from sos import servers
    application = servers.run_application()

elif __name__ == "__main__"  :
    import os, sys
    _h = os.path.join(
        os.path.split(os.path.abspath(os.path.dirname(__file__), ), )[0],
        "lib",
        "python%s" % ".".join(map(str, sys.version_info[:2], ), ),
        "site-packages",
    )
    if os.path.exists(_h) :
        sys.path.insert(0, _h, )

    from sos import servers
    servers.run_script(__file__, )

