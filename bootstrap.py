#!/usr/bin/env python
import os, sys, subprocess, parser

# Determine if Python 2.7, also import argparse
try:
    import argparse
except ImportError:
    sys.stderr.write("Unable to import argparse. "
                     "Maybe you're using the wrong version of Python. "
                     "This project requires Python 2.7.x\n\n")
    sys.exit(-1)

# Determine if we're forcing install regardless of virtualenv
parser = argparse.ArgumentParser()
parser.add_argument('--force', '-f', action='store_true')

force = parser.parse_args().force

if "VIRTUAL_ENV" not in os.environ:
    if not force:
        sys.stderr.write("$VIRTUAL_ENV not found. "
                         "We recommend using a virtualenv to proceed. "
                         "If you wish to install modules to Python's "
                         "global site packages dir, please call this "
                         "command with the --force option.\n\n")
        sys.exit(-1)
    virtualenv = None     
else:
    virtualenv = os.environ["VIRTUAL_ENV"]

file_path = os.path.dirname(__file__)
subprocess.call(["pip", "install", "--requirement",
                os.path.join(file_path, "requirements.txt")])
