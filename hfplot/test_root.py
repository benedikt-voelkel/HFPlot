"""Check if ROOT is available

"""

import sys

ROOT_CHECKED = False

try:
    from ROOT import gROOT
    if not ROOT_CHECKED:
        print(f"\n>>> Using ROOT {gROOT.RootVersionCode()} <<<\n")
        ROOT_CHECKED = True
except ImportError:
    print("ROOT installation not found but required")
    sys.exit(1)
