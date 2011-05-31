# -*- coding: utf-8 -*-

import sys
if not hasattr(sys, "version_info") or sys.version_info < (2, 6, ):
    raise RuntimeError("sos requires Python 2.6 or later.")
del sys


