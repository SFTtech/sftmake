#!/usr/bin/python3
from logger import logger, LogWriter, LogStorage
from logger.levels import *

#now follows some example usage code
logger.addsink(LogWriter())
logger.addsink(LogStorage(dumpatexit="/tmp/asdf"))

important("ohai")
message("Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.")
important("kthxbai")
