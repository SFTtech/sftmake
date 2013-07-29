#!/usr/bin/python3
#
# This file is part of sftmake.
#
# License: GPLv3 or later, no warranty, etc
#
# Purpose of this file:
# * classes for managing build elements (sources, targets, headers, etc)
#

import os.path
import os
import re
from logger.levels import *


import util
from util.path import abspath,smpath,relpath
from util.path import generate_oname
import conf
import subprocess
import shlex



class BuildElement:

	def __init__(self, name):
		self.depends = set()
		self.depends_wanted = set()
		self.depends_finished = set()
		self.name = smpath(name)
		self.inname = abspath(name)
		self.outname = ""
		self.encname = ""
		self.crun = ""
		self.prebuild = ""
		self.postbuild = ""
		self.needs_build = False
		self.ready = False
		# the parent BuildElements, which are blocked by this one:
		self.blocks = set()
		self.worker = None
		self.loglevel = 2	# standard value?
		self.exitstate = 0
		self.finished = False
		self._inmtime = 0
		self._outmtime = 0
		self._inname_exists = (False, False) #first: was checked, second: exists
		self._outname_exists = (False, False)

	def run(self):
		raise NotImplementedError("Implement this shit for a working compilation...")

	def _run(self, elem_type):
		'''generic run method for sourcefiles and targets'''

		ret = 0  #return value storage

		if elem_type == 0: #target
			action = "linking"
		elif elem_type == 1: #sourcefile
			action = "compiling"
			with self.worker.manager.filesys_lock:
				dirname = os.path.dirname(self.outname)
				os.makedirs(dirname, exist_ok=True)
				#TODO: check if dir is writable

		if self.prebuild:
			failat = "prebuilding"
			self.worker.wprint("prebuild for " + repr(self) + ": \"" + self.prebuild + "\"")
			ret = subprocess.call(self.prebuild, shell=True)

		if ret == 0:
			failat = action
			self.worker.wprint(" == "+action+" -> " + repr(self))
			self.worker.wprint(" EXEC:: " + self.crun)

			## compiler is launched here:
			cexec = subprocess.Popen(shlex.split(self.crun), shell=False, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) #, universal_newlines=True)

			for line in cexec.stdout:
				self.worker.wprint(str(line, "UTF-8"))

			ret = cexec.wait()
			## tada, that was it.

			self.worker.wprint("== done "+action+" -> " + repr(self))

		if ret == 0:
			if self.postbuild:
				failat = "postbuilding"
				self.worker.wprint("postbuild for " + repr(self) + ": \"" + self.postbuild + "\"")
				ret = subprocess.call(self.postbuild, shell=True)

		if ret > 0:
			self.worker.wprint(repr(self) + " Error " + str(ret) + " when " + failat  + " ===============")
			self.exitstate = ret
		else:
			self.exitstate = 0

	def equals(self, other):
		#TODO: print, what test failed
		#print(repr(self) + " equal test == " + repr(other))

		if id(self) == id(other):
			return True

		if not type(other) == type(self):
			debug("type check failed")
			return False

		if not self.outname == other.outname:
			return False

		if not self.prebuild == other.prebuild:
			return False

		if not self.postbuild == other.postbuild:
			return False

		if not self.loglevel == other.loglevel:
			return False

		#print(repr(self) + '(' + str(id(self)) + ')' + " is equal to " + repr(other) + '(' + str(id(other)) + ')')
		return True

	def add_deps_to_manager(self, manager):
		'''adds all dependencies to a JobManager, recursively'''

		#already submitted jobs are ignored
		for f in self.depends:
			f.add_deps_to_manager(manager)
		manager.submit_single(self)

	def finish(self, manager=None):
		'''
		upon a successful run, set finished to True
		notify parents (blocks) that this dependency is ready
		'''

		self.finished = True

		domgr = not (manager == None)

		for parent in self.blocks:
			parent.depends.remove(self)

			#TODO: suppress this via config
			parent.depends_finished.add(self)

			#print(repr(self) + " finished -> left parent.depends=" + repr(parent.depends))

			if domgr and parent.ready_to_build():
				manager.pending_jobs.remove(parent)
				manager.ready_jobs.add(parent)

	def add_dependency(self, newone):
		'''
		a dependency to this compilation job
		detects whether newone is a list or a single BuildElement
		'''

		if type(newone) == list:
			for e in newone:
				if not isinstance(newone, BuildElement):
					raise Exception("only BuildElements can be added as a dependency for another BuildElement")
				self.add_single_dependency(e)

		else:
			if not isinstance(newone, BuildElement):
				raise Exception("only BuildElements can be added as a dependency for another BuildElement")
			self.add_single_dependency(newone)

	def add_single_dependency(self, newone):
		'''this element will be dependent on this new dependeny'''
		debug(repr(self) + " -> adding dependency " + repr(newone))
		newone.blocks.add(self)
		self.depends.add(newone)

	def move_blocked(self, old, new):
		'''renames (moves) a parent'''
		if not isinstance(old, BuildElement) \
		or not isinstance(new, BuildElement):
			raise Exception("only BuildElements can be used to move blocked parents")

		for dependency in self.depends:
			if old in dependency.blocks:
				dependency.blocks.remove(old)
				dependency.blocks.add(new)

	def inmtime(self):
		if self._inmtime == 0:
			if self.inname_exists():
				self._inmtime = os.path.getmtime(self.inname)
			else:
				raise Exception(repr(self) + ".inname doesn't exist, so no mtime")
		return self._inmtime

	def outmtime(self):
		if self._outmtime == 0:
			if self.outname_exists():
				self._outmtime = os.path.getmtime(self.outname)
			else:
				raise Exception(repr(self) + ".outname doesn't exist, so no mtime")
		return self._outmtime

	def outname_exists(self):
		ch, res = self._outname_exists
		if ch:
			return res
		else:
			exists = os.path.isfile(self.outname)
			self._outname_exists = (True, exists)
			return exists

	def inname_exists(self):
		ch, res = self._inname_exists
		if ch:
			return res
		else:
			exists = os.path.isfile(self.inname)
			self._inname_exists = (True, exists)
			return exists

	def check_needs_build(self):
		'''
		checks if this build element needs a compile

		look at the mtimes n stuff for that.

		then, set self.needs_build to the correct value
		should be overridden if appropriate (e.g. header file)
		'''

		if self.outname_exists():
			if self.inname:
				if self.inname_exists():
					im = self.inmtime()
					om = self.outmtime()
					#print("checking mtime of " + self.inname + " in:" + str(im) + " out:" + str(om))

					if om < im:
						self.needs_build = True
						return True

				else:
					#inname does not exist
					raise Exception("requested " + repr(self) + ".inname (" + self.inname + ") does not exist")

		else: # outname does not exist
			self.needs_build = True
			return True

		#only check dependencies, if we don't need a build (we'd have returned then)
		for d in (self.depends | self.depends_finished):
			try:

				if d.check_needs_build():
					self.needs_build = True

				# check for modification times
				if self.outname_exists() and d.outname_exists():
					dm = d.outmtime()
					om = self.outmtime()

					if dm > om:
						print("==> Build needed: dependency " + repr(d) + " is newer than " + self.outname)
						self.needs_build = True
						return True

			except OSError as e:
				raise e

		return self.needs_build

	def ready_to_build(self):
		'''when all dependencies are done, return true'''
		if len(self.depends) > 0:
			self.ready = False
		else:
			self.ready = True
		return self.ready

	def text(self, depth=0):
		'''inname, outname, ready, encname, blocks'''
		space = ''.join(['\t' for i in range(depth)])
		out = space + "++++ " + str(type(self)) + " " + str(id(self)) + "\n"

		if self.inname:
			out += space + "* Input filename: " + self.inname + "\n"

		if self.outname:
			out += space + "* Output filename: " + self.outname + "\n"

		if self.encname:
			out += space + "* Encoded name: " + self.encname + "\n"

		if self.crun:
			out += space + "* c-run: " + self.crun + "\n"

		#if len(self.depends_wanted) > 0:
		out += space + "* wanted dependencies: " + str(self.depends_wanted) + "\n"

		out += space + "--- status: " + str(self.exitstate) + " ---\n"

		deps_done = len(self.depends_finished)
		deps_pending = len(self.depends)
		deps_sum = deps_done + deps_pending

		if deps_sum > 0:
			deps_percent =  "{0:.2f}".format(float(deps_done/deps_sum) * 100)

			out += space + "--- deps: ["
			out += str(deps_done) + "/" + str(deps_sum) + "] "
			out += "[" + deps_percent + "%"
			out += "] ---\n"

			if len(self.depends) > 0:
				out += space + "--- pending dependencies:\n"
				for f in self.depends:
					out += f.text(depth + 1)
					out += space + "---\n"

			if len(self.depends_finished) > 0:
				out += space + "--- finished dependencies:\n"

				for f in self.depends_finished:
					out += f.text(depth + 1)
					out += space + "---\n"
		else:
			out += space + "* NO dependencies\n"

		if self.ready:
			if self.finished:
				out += space + "* BUILT SUCCESSFULLY\n"
			else:
				if self.exitstate != 0:
					out += space + "* FAILED\n"
				else:
					out += space + "* READY TO BUILD\n"
		else:
			if len(self.depends) > 0:
				out += space + "* BLOCKED BY DEPENDENCIES\n"
			else:
				out += space + "* NOT READY\n"

		out += space + "++++\n"
		return out

	def __str__(self):
		return self.text()


class WantedDependency(BuildElement):
	"""if a dependency is wanted, this type is used."""

	def __init__(self, wname):
		super().__init__(wname)
		self.inname = None
		self.outname = relpath(wname)

	def equals(self, other):
		'''used to check if "other" is the wanted dependency'''

		debug(repr(self) + " testing with " + repr(other))

		#we only know the output name
		if not self.outname == other.outname:
			return False

		#TODO: maybe come up with ids or other properties that identify
		#which dependency is wanted.

		return True

	def run(self):
		raise Exception("WTF why is this placeholder even executed???")

	def __repr__(self):
		return "W{" + self.outname + "}"


class HeaderFile(BuildElement):
	"""headerfile for a source file, never needs to be built"""

	#random numbers for enum behavior
	externalheader = 18387
	projectheader = 52838

	def __init__(self, hname):
		super().__init__(hname)

		if util.path.in_smdir(self.inname):
			self.headertype = HeaderFile.projectheader
			self.outname = relpath(self.inname)
		else:
			self.headertype = HeaderFile.externalheader
			self.outname = self.inname

	def check_needs_build(self):
		self.needs_build = False
		return False

	def equals(self, other):
		if id(self) == id(other):
			return True

		if not type(self) == type(other):
			return False

		if not self.outname == other.outname:
			return False

		return True

	def text(self, depth=0):
		space = ''.join(['\t' for i in range(depth)])
		return space + repr(self) + "\n"

	def run(self):
		return Exception("HeaderFiles should never be run. skip them.")

	def __repr__(self):
		if self.headertype == HeaderFile.externalheader:
			isexternal = "{ext}"
		else:
			isexternal = "{project}"

		return isexternal + " " + self.outname


class SourceFile(BuildElement):
	"""a source file like lolmysource.c"""

	def __init__(self, filename):
		super().__init__(filename)
		self.objdir = ""
		self.mdfile = ""
		#self.outname will be set by the order filling


	def run(self):
		'''this method is called to compile the object file from the source.'''
		self._run(1)

	def __repr__(self):
		return self.inname

	def __str__(self):
		return self.text()


class BuildTarget(BuildElement):
	'''A build target is a library or a executable binary'''

	def __init__(self, tname):
		super().__init__(tname)
		self.name = tname
		self.outname = relpath(tname)
		self.encname = generate_oname(self.outname)
		self.inname = None #target's inname must not be used

	def equals(self, other):
		if id(self) == id(other):
			return True

		if not type(self) == type(other):
			return False

		if not self.outname == other.outname:
			return False

		if not self.crun == other.crun:
			return False

		if not self.prebuild == other.prebuild:
			return False

		if not self.postbuild == other.postbuild:
			return False

		if not self.loglevel == other.loglevel:
			return False

		return True

	'''called when the target shall be linked'''
	def run(self):
		self._run(0)

	def __str__(self):
		return self.text()

	def __repr__(self):
		return self.outname
