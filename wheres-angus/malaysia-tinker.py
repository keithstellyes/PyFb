# for tinkering around in REPL

import json, sys
sys.path.append('..')
from pyfb import util as pyfbutil
import wheresangus

malaysia = json.load(open('malaysia.json', 'r'))