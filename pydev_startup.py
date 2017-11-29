import os
import sys

sys.path.append(os.getcwd())

import ptvsd

ptvsd.enable_attach(secret='gae', address=('0.0.0.0', 3000))

print "Google App Engine has started, ready to attach the debugger."