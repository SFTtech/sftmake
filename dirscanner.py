#!/usr/bin/env python3

import os

"""
scan from current directory and find project root directory (by file 'sftmake')

project root:    ^/sftmake

config files:

per dir:         ^/foo/bar/smfile
per target:      ^/foo/libsftcall.target.smtarget
per source:      ^/foo/main.cpp.smsrc
"""

def create_smtree():
	smroot = find_smroot()
	smfilepaths = []
	for (path, dirs, files) in os.walk(smroot):
		# filter hidden directories
		dirs[:] = [d for d in dirs if not d[0] == '.']

		for f in files:
			if f[0] not in '#.' and (f == "smfile" or f.endswith(".smfile") or f.endswith(".sm")):
				smfilepaths.append(os.path.join(path, f))

	print(smfilepaths)


def find_smroot():
	path = os.path.abspath('.')
	while(not os.path.isfile(path + "/smfile")):
		if(path == "/"):
			raise Exception("No smfile found")
		else:
			path = os.path.abspath(path + '/..')
	return path

