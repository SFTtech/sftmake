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

project root:   ^/smfile       /root.smfile
dir + subdir:   ^/foo/bar/dir.smfile           /dir.sm
link target:    ^/foo/lolbinary.target.smfile  /lolbinary.target.sm  /lolbinary.smtarget
per source:     ^/foo/srcfile.cpp.smfile       /srcfile.cpp.src.sm   /srcfile.cpp.sm  /srcfile.cpp.smsrc
"""


class smtree:

	#regexes to ignore files/folders
	ignorenames = r"(__pycache__$|#.*|\..+|(M|m)akefile)"

	#define regexes for the smfile types
	rootsmfile_names  = r"^(smfile|root\.smfile)$"
	directorysm_names = r"^(dir|directory)\.(sm|smfile)$"
	targetsm_names    = r"^.+\.target\.(sm|smfile)$"
	sourcesm_names    = r"^(.+)\.(src|source)\.(sm|smfile)$"

	def __init__(self, rootpath):
		self.smroot = rootpath  #path to project dir

		self.root_smfile = None  #the project root smfile
		self.smfiles = []

		self.scanned_all_files = False

		#TODO: these functions shoule be disablable
		self.find_files()


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

				#determine smfile type (root, directory, target, source, inline)
				#is this a root smfile?
				if re.match(self.rootsmfile_names, f):
					if self.root_smfile != None:
						raise Exception("Another root smfile candidate found: " + path + "/" + f)
					else:
						# we found the root smfile
						self.root_smfile = rootsmfile(path, f)
						self.smfiles.append(self.root_smfile)
						continue

				#is this a directory smfile?
				if re.match(self.directorysm_names, f):
					# a directory-smfile was found
					self.smfiles.append(dirsmfile(path, f))
					continue

				#is this a target smfile?
				if re.match(self.targetsm_names, f):
					# a target-smfile was found
					self.smfiles.append(targetsmfile(path, f))
					continue

				#is this a source smfile?
				if re.match(self.sourcesm_names, f):
					# a source-smfile was found
					self.smfiles.append(srcsmfile(path, f))
					continue

				#if we reach this point, the file is no smfile.
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
		"""
		returns (path, filename) as the project root smfile
		"""

		return self.root_smfile

	def __repr__(self):
		return "smfile-tree: " + str(len(self.smfiles)) + " smfiles found"

	def __str__(self):
		txt = repr(self) + "\n"
		txt += "found smfiles:\n"

		for sf in self.smfiles:
			txt += "\t" + str(sf)

		return txt


class smfile:
	#types of smfiles:

	rootsmfile = util.EnumVal("root-smfile")
	dirsmfile = util.EnumVal("directory-smfile")
	targetsmfile = util.EnumVal("target-smfile")
	srcsmfile = util.EnumVal("source-smfile")
	inlinesmfile = util.EnumVal("inline-smfile")

	def __init__(self, path, filename, smtype):
		self.path = path
		self.filename = filename
		self.fullname = self.path + "/" + self.filename

		if not smtype in [self.rootsmfile, self.targetsmfile, self.dirsmfile, self.srcsmfile, self.inlinesmfile]:
			raise Exception("unknown smfile type '" + repr(smtype) + "'")
		else:
			self.smtype = smtype

	def __str__(self):
		txt = repr(self) + "\n"
		return txt

	def __repr__(self):
		return "smfile " + str(type(self)) + " -> " + self.fullname

class rootsmfile(smfile):
	def __init__(self, path, filename):
		smfile.__init__(self, path, filename, self.rootsmfile)

class dirsmfiles(smfile):
	def __init__(self, path, filename):
		smfile.__init__(self, path, filename, self.dirsmfile)

class targetsmfile(smfile):
	def __init__(self, path, filename):
		smfile.__init__(self, path, filename, self.targetsmfile)

class srcsmfile(smfile):
	def __init__(self, path, filename):
		smfile.__init__(self, path, filename, self.srcsmfile)

		smfilename = self.path + "/" + self.filename
		matchingfile = re.search(smtree.sourcesm_names, smfilename)
		if matchingfile:
			realfilename = matchingfile.group(1)

			if not os.path.isfile(realfilename):
				raise Exception("source smconfig found for nonexistant file \n\t" + realfilename)

		else:
			raise Exception("wtf internal fail, it should always match...")

class inlinesmfile(smfile):
	def __init__(self, path, filename):
		smfile.__init__(self, path, filename, self.inlinesmfile)
