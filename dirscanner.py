#!/usr/bin/env python3

# this file is part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# directory scanner for locating smfiles
# and scanning for inline configuration
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

	#regexes to ignore files/folders
	ignorenames = r"(__pycache__$|#.*|\..+)"

	#define regexes for the smfile types
	rootsmfile_names  = r"^(smfile|root\.smfile)$"
	directorysm_names = r"^(dir|directory)\.(sm|smfile)$"
	targetsm_names    = r"^.+\.target\.(sm|smfile)$"
	sourcesm_names    = r"^.+\.(src|source)\.(sm|smfile)$"

	def __init__(self, rootpath):
		self.smroot = rootpath  #path to project dir

		self.smfiles = []       #list of all smfile, relpaths
		self.files = []         #list of all files, relpaths
		self.directories = []   #list of all directories, relpath

		self.scanned_all_files = False
		self.scanned_smfiles = False

		#TODO: these functions shoule be disablable
		self.find_all_files()


	def find_files(self):
		"""
		scan the whole directory tree for files (including smfiles)
		and store them into a big file array
		"""

		if self.scanned_all_files:
			return

		print(os.getcwd())
		print("scanning " + self.smroot + " for files")
		for (path, dirs, files) in os.walk(self.smroot):

			print("looking in path " + path + "for contents")

			#check whether we should look into the current folder (path)
			ignorepath = False
			if re.match(self.ignorenames, path):
				ignorepath = True

			#the current path will be ignored
			if ignorepath:
				continue

			#all files in the current folder (path)
			for f in files:
				ignorefile = False
				if re.match(self.ignorenames, f):
					ignorefile = True

				if ignorefile:
					continue

				print(path + "/" + f)

			#all folders in the current folder (path)
			for d in dirs:
				ignoredir = False
				if re.match(self.ignorenames, d):
					ignoredir = True

				if ignoredir:
					continue

				print(path + "/" + d)

		self.scanned_all_files = True

	def get_root_smfile(self):
		return "lolnope"
