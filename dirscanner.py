#!/usr/bin/env python3

# this file is part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# main sftmake entry file, currently using conf-pysmfile
# for configuration
#
# (c) 2013 [sft]technologies, jonas jelten


import os
import re
import util

"""
scan from project root directory and cascade into all subfolders

project root:  ^/smfile
dir + subdir:  ^/foo/bar/dir.smfile           /dir.sm
link target:   ^/foo/lolbinary.target.smfile  /lolbinary.target.sm
per source:    ^/foo/srcfile.cpp.smfile       /srcfile.cpp.src.sm   /srcfile.cpp.sm
"""




class smtree:

	#use these regexes to ignore files/folders
	ignorenames = ["__pycache__", r"\..*"]

	def __init__(self, rootpath):
		self.smroot = rootpath  #abspath to project dir
		self.filestructure = [] #filestructure, starting at ^, elem=(foldername, [elem, ...])
		self.smfiles = []       #list of all smfile, relpaths
		self.files = []         #list of all files, relpaths

	def find_smfiles(self):
		smf_lambda = lambda d = False
		self.smfiles = filter(smf_lambda, self.files)

	def find_all_files(self):
		for (path, dirs, files) in os.walk(smroot):
			# filter hidden directories

			f_lambda = lambda d = False
			dirs = filter(f_lambda , dirs)
			dirs[:] = [d for d in dirs if re.match(, d)]

			for f in files:
				if f[0] not in '#.' and (f == "smfile" or f.endswith(".smfile") or f.endswith(".sm")):
					self.smfilepaths.add(os.path.join(path, f))
