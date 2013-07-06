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
from logger import *

"""
scan from project root directory and cascade into all subfolders

project root:   ^/smfile       /root.smfile
dir + subdir:   ^/foo/bar/dir.smfile           /dir.sm
link target:    ^/foo/lolbinary.target.smfile  /lolbinary.target.sm  /lolbinary.smtarget
per source:     ^/foo/srcfile.cpp.smfile       /srcfile.cpp.src.sm   /srcfile.cpp.sm  /srcfile.cpp.smsrc
"""


class smtree:

	#regexes to ignore files/folders
	ignorenames = re.compile(r"(__pycache__$|#.*|(M|m)akefile)|^.git|^\.[^/]")

	#define regexes for the smfile types
	rootsmfile_names  = re.compile(r"^(smfile|root\.smfile)(\.py)?$")
	directorysm_names = re.compile(r"^((dir|directory)\.(sm|smfile)|smdir)(\.py)?$")
	targetsm_names    = re.compile(r"^(.+)\.(target\.(sm|smfile)|smtarget)(\.py)?$")
	sourcesm_names    = re.compile(r"^(.+)\.((src|source)\.(sm|smfile)|smsrc)(\.py)?$")

	def __init__(self, rootpath):
		self.smroot = rootpath  #path to project dir

		self.root_smfile = None  #the project root smfile
		self.smfiles = []
		self.regular_files = []

		self.find_files()

	def get_root_smfile(self):
		"""
		returns the project root smfile as object of rootsmfile class
		"""

		if self.root_smfile == None:
			raise Exception("no root smfile found for this smtree")
		return self.root_smfile

	def get_target_smfiles(self):
		return [smfile for smfile in self.smfiles if isinstance(smfile, targetsmfile)]

	def get_source_smfiles(self):
		return [smfile for smfile in self.smfiles if isinstance(smfile, srcsmfile)]

	def get_targets(self):
		raise NotImplementedError()

	def get_sources(self):
		return self.regular_files

	def find_files(self):
		"""
		scan the whole directory tree for files (including smfiles)
		and store them into a big file array
		"""

		debug("scanning " + self.smroot + " for files")
		for (path, dirs, files) in os.walk(self.smroot):

			debug("looking in path " + path + " for contents")

			#check whether we should look into the current folder (path)
			ignorepath = False
			if self.ignorenames.match(path):
				ignorepath = True

			#the current path will be ignored
			if ignorepath:
				debug("ignoring current path: " + path)
				continue

			#all folders in the current folder (path)
			for d in dirs:
				ignoredir = False
				if self.ignorenames.match(d):
					ignoredir = True
					dirs.remove(d) #so os.walk doesn't visit the dir
					debug("removing from list to visit: " + d)

				if ignoredir:
					continue

			#all files in the current folder (path)
			for f in files:
				ignorefile = False
				if self.ignorenames.match(f):
					ignorefile = True

				if ignorefile:
					continue

				fullpath = path + "/" + f

				#determine smfile type (root, directory, target, source, inline)
				#is this a root smfile?
				if self.rootsmfile_names.match(f):
					if self.root_smfile != None:
						raise Exception("Another root smfile candidate found: " + path + "/" + f + "\n conflicting with " + repr(self.root_smfile))
					else:
						# we found the root smfile
						self.root_smfile = rootsmfile(path, f)
						self.smfiles.append(self.root_smfile)
						debug("root-smfile -> " + fullpath)
						continue

				#is this a directory smfile?
				if self.directorysm_names.match(f):
					# a directory-smfile was found
					self.smfiles.append(dirsmfile(path, f))
					debug("directory-smfile -> " + fullpath)
					continue

				#is this a target smfile?
				if self.targetsm_names.match(f):
					# a target-smfile was found
					self.smfiles.append(targetsmfile(path, f))
					debug("target-smfile -> " + fullpath)
					continue

				#is this a source smfile?
				if self.sourcesm_names.match(f):
					# a source-smfile was found
					self.smfiles.append(srcsmfile(path, f))
					debug("source-smfile -> " + fullpath)
					continue

				#if we reach this point, the file is no smfile.
				debug("regular file => " + fullpath)

				rfile = simple_file(path, f)
				self.regular_files.append(rfile)

	def __repr__(self):
		return "smfile-tree: " + str(len(self.smfiles)) + " smfiles found"

	def __str__(self):
		txt = repr(self) + "\n"
		txt += "found smfiles:\n"

		for sf in self.smfiles:
			txt += "\t" + str(sf)

		txt += "\nfound regular files:\n"

		for f in self.regular_files:
			txt += "\t" + str(f)
		return txt



class simple_file:
	"""
	any ordinary file...
	"""
	def __init__(self, path, filename):
		self.directory = path
		self.filename = filename
		self.fullname = self.directory + "/" + self.filename
		self._smname = None
		self._dirsmname = None

	def __str__(self):
		txt = repr(self) + "\n"
		return txt

	def __repr__(self):
		return "file [" + self.fullname + "]"

	def content(self):
		with open(self.fullname) as f:
			return f.read()

	def get_smname(self):
		if self._smname == None:
			self._smname = util.smpath(self.fullname)

		return self._smname

	def get_dir_smname(self):
		if self._dirsmname == None:
			self._dirsmname = util.smpath(self.directory)

		return self._dirsmname


class smfile(simple_file):

	def __init__(self, path, filename):
		super().__init__(path, filename)

		self.realfilename = None
		self.realsmfilename = None
		self.smhandler = None

	def __repr__(self):
		return "smfile " + str(type(self)) + " -> " + self.fullname

	def smcontent(self):
		"""
		content relevant for sftmake, i.e. the whole smfile content
		"""
		return self.content()

	def create_handler(self):
		"""
		creates a wrapper object that is used for interpreting the files
		contents.  conf_smfile is used for interpreting.
		"""
		import conf_smfile
		self.smhandler = conf_smfile.smfile_factory(self)
		return self.smhandler

	def get_handler(self):
		return self.smhandler

	def get_associated_smname(self):
		raise NotImplementedError("This has to be implemented for the specific smfile types, you are calling the method of the base class.")


class rootsmfile(smfile):
	def __init__(self, path, filename):
		super().__init__(path, filename)

class dirsmfiles(smfile):
	def __init__(self, path, filename):
		super().__init__(path, filename)

	def get_associated_smname(self):
		return self.get_dir_smname()

class assignmentsmfile(smfile):
	def __init__(self, path, filename):
		super().__init__(path, filename)

	def __str__(self):
		txt = super().__repr__() + " for " + self.realfilename + "\n"
		return txt

class targetsmfile(assignmentsmfile):
	def __init__(self, path, filename):
		assignmentsmfile.__init__(self, path, filename)

		matchingtarget = re.search(smtree.targetsm_names, self.fullname)
		if matchingtarget:
			targetname = matchingtarget.group(1)
			self.realfilename = targetname

		else:
			raise Exception("internal error, the target always has to match")

	def get_associated_smname(self):
		if self.realsmfilename == None:
			self.realsmfilename = util.smpath(self.realfilename)
		return self.realsmfilename


class srcsmfile(assignmentsmfile):
	def __init__(self, path, filename):
		super().__init__(path, filename)

		matchingfile = re.search(smtree.sourcesm_names, self.fullname)
		if matchingfile:
			realfilename = matchingfile.group(1)

			if not os.path.isfile(realfilename):
				raise Exception("source smconfig found for nonexistant file \n\t" + realfilename)

			self.realfilename = realfilename

		else:
			raise Exception("wtf internal fail, it should always match...")

	def get_associated_smname(self):
		if self.realsmfilename == None:
			self.realsmfilename = util.smpath(self.realfilename)
		return self.realsmfilename


class inlinesmfile(smfile):
	"""
	only the inlined sftmake-relevant part of a project's source file
	"""
	def __init__(self, path, filename):
		super().__init__(path, filename)

	def smcontent(self):
		#TODO: extract the inline content and return it
		raise NotImplementedError("inline configs not supported yet")

	def get_associated_smname(self):
		return self.get_smname()
