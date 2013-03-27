#!/usr/bin/env python3

import os

"""
scan from current directory and find project root directory (by smfile)

project root:		^/smfile
dir + subdir:		^/foo/bar/dir.smfile		/dir.sm
link target:		^/foo/lolbinary.target.smfile	/lolbinary.target.sm
per source:			^/foo/srcfile.cpp.smfile	/srcfile.cpp.src.sm	/srcfile.cpp.sm
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

