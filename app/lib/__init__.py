import sys
import os

_lib_path = os.path.abspath(os.path.dirname(__file__))

if not _lib_path in sys.path:
    sys.path.append(_lib_path)
