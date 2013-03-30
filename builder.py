#!/usr/bin/python3
#
# This file is part of sftmake.
#
# License: GPLv3 or later, no warranty, etc
#
# Purpose of this file:
# * convert sftmake variables to BuildOrders
# * execute a BuildOrder (compile stuff)
# * show cat pictures
#
#

import multiprocessing
import os.path
import pprint
import random
import re
import shlex
import subprocess
import threading
import time

import util
import conf


class vartest:
	def __init__(self, arg):
		self.l = arg

	def get(self, a = ""):
		return self.l

	def __repr__(self):
		if self.l == None:
			return "None"
		else:
			return "vartest:\t" + pprint.pformat(self.l)

class vartestadv:
	def __init__(self, init=dict()):
		self.l = init

	def get(self, param):
		print("getting [" + param + "]: ", end='')
		ret = self.l[param]
		print(str(ret))
		return ret

	def addv(self, key, val):
		self.l[key] = val

	def pushv(self, key, val):
		if key in self.l:
			self.l[key].append(val)
		else:
			self.l[key] = [val]

	def __repr__(self):
		return "vartestadvanced:\t" + pprint.pformat(self.l, width=300)

if not "assembled" in globals():
	from util import smpath,relpath,generate_oname


#test purpose only
variables = dict()
variables["c"] = vartest("gcc")
variables["build"] = vartest({"^/lolbinary", "^/liblol.so"})
variables["filelist"] = vartest({'^/main.c', '^/both.c', '^/library0.c', '^/library1.c'})
variables["cflags"] = vartest("-O1 -march=native")
variables["ldflags"] = vartest("-L. -llol")
variables["objdir"] = vartest("^/.objdir")

variables["use"] = vartestadv()
variables["usedby"] = vartestadv()
variables["depends"] = vartestadv()
variables["depends"].addv("^/main.c", set())
variables["depends"].addv("^/both.c", set())
variables["depends"].addv("^/library0.c", set())
variables["depends"].addv("^/library1.c", set())
variables["depends"].addv("^/lolbinary", {"^/liblol.so"})
variables["depends"].addv("^/liblol.so", set())

variables["depends"].addv("^/liblol.so-^/both.c", set())
variables["depends"].addv("^/liblol.so-^/library0.c", set())
variables["depends"].addv("^/liblol.so-^/library1.c", set())
variables["depends"].addv("^/lolbinary-^/main.c", set())
variables["depends"].addv("^/lolbinary-^/both.c", set())

variables["use"].addv("^/lolbinary", {'^/both.c', '^/main.c'})
variables["use"].addv("^/liblol.so", {'^/both.c', '^/library0.c', '^/library1.c'})
variables["usedby"].addv("^/main.c", set())
variables["usedby"].addv("^/both.c", set())
variables["usedby"].addv("^/library0.c", set())
variables["usedby"].addv("^/library1.c", set())

variables["autodepends"] = vartest("MD")
variables["prebuild"] = vartest("echo startin build")
variables["postbuild"] = vartest("echo finished build")
variables["loglevel"] = vartest("2")

print("var initialisation: \n")
pprint.pprint(variables)
print("\n\n\n")


confinfo = {}
conf_base = conf.Config([], '^', conf.Config.BASE)
conf_main = conf.Config([conf_base], '^', conf.Config.SRC)
conf_lib0 = conf.Config([conf_base], '^', conf.Config.SRC)
conf_lib1 = conf.Config([conf_base], '^', conf.Config.SRC)
conf_both = conf.Config([conf_base], '^', conf.Config.SRC)
conf_lib = conf.Config([conf_base], '^', conf.Config.SRC)
conf_bin = conf.Config([conf_base], '^', conf.Config.SRC)
confinfo["^/main.c"] = conf_main
confinfo["^/library0.c"] = conf_lib0
confinfo["^/library1.c"] = conf_lib1
confinfo["^/both.c"] = conf_both
confinfo["^/liblol.so"] = conf_lib
confinfo["^/lolbinary"] = conf_bin


"""
'default' is the absolute root configuration, and consists of the internal defaults
confinfo["default"] = Config(parents = [], directory = '^', kind = Config.BASE)

#src-config erzeugen
confinfo["^/folder/file.c"] = Config(parents = ["^/folder"], directory = "^/folder", kind = Config.SRC)
#src-for-target-config erzeugen
confinfo[src + "-" + target] = Config(parents = [src, target], directory = confinfo[src].directory, kind = Config.SRCFORTARGET)

inheritance hierarchy of a src file:
^/folder/file.c         ^/folder
^/folder                ^/folder
^                       ^
args                    ^
default                 ^

confinfo[src] = Config(parents = [src-folder], directory = src-folder-stuff, kind = Config.SRC)
#variable befuellen
variables["c"].addval([Val("g++", None, Val.MODE_APPEND)], "^/folder/file.c")
"""


#TODO: when buildelements are used by multiple parents, detect that (e.g. header files) (respecting the differing variable values!)
#This means: extend the current tree model of dependencies to a graph model.

#TODO: colored output

#TODO: output queue, fixing thread interferences with msgs containing newlines

#TODO: unit test class

#TODO: pre/postrun must not be inherited, only if explicitly specified

#TODO: add more shell commands, e.g. all dependencies ready

#TODO: add testing features and bisect support





class BuildWorker:
	"""A worker thread that works and behaves like a slave. Be careful, it bites."""

	def __init__(self, manager, num=-1):
		self.thread = threading.Thread(target=self.run)
		self.manager = manager
		self.num = num
		self.job = None		#The BuildElement currently being processed by this worker

	def run(self):
		print("" + repr(self) + ": started")
		while True:
			self.job = self.manager.get_next()
			if self.job == None:
				#no more jobs available
				#so the worker can die!
				break

			print(repr(self) + ": fetched job ->\t" + repr(self.job))
			self.job.worker = self

			if self.job.check_needs_build():
				#TODO: same output colors for each worker
				print("" + repr(self) + ": making job ->\t" + repr(self.job))
				self.job.run()
			else:
				print("" + repr(self) + ": skipped job ->\t" + repr(self.job))

			self.manager.finished(self.job)
		print(repr(self) + ": dead")

	def start(self):
		self.thread.start()

	def join(self):
		self.thread.join()

	def __repr__(self):
		return "[worker [" + str(self.num) + "]]"


class JobManager:
	"""thread manager for invoking the compilers"""

	def __init__(self, max_workers=util.get_thread_count()):
		self.workers = []

		self.pending_jobs  = set()		# jobs that will be processed sometime
		self.ready_jobs    = set()		# jobs that are ready to be executed
		self.running_jobs  = set()		# currently executing jobs
		self.finished_jobs = set()		# jobs that were executed successfully
		self.failed_jobs   = set()		# jobs that exited with errors
		self.max_workers   = max_workers	# worker limitation

		self.error = 0

		self.job_lock = threading.Condition()

	def queue_order(self, order):
		if not isinstance(order, BuildOrder):
			raise Exception("Only a whole BuildOrder can be processed")

		for target in order.targets:
			self.submit(target)

		#TODO: respect verbosity and use repr/str/none/text()/whatevvur
		#print("\n\n Submitted: " + order.text())



	def submit(self, job):
		"""insert a job and it's dependencies in the execution queue"""
		if not isinstance(job, BuildElement):
			raise Exception("only BuildElements can be submitted")

		job.add_deps_to_manager(self)

	def submit_single(self, job):
		"""insert a single job in the correct job queue"""
		if not isinstance(job, BuildElement):
			raise Exception("only BuildElements can be submitted")

		with self.job_lock:
			if job.ready_to_build():
				self.ready_jobs.add(job)
			else:
				self.pending_jobs.add(job)

	def finished(self, job):
		'''must be called when a job is done executing'''
		with self.job_lock:
			if job.exitstate == 0:
				self.running_jobs.remove(job)
				self.finished_jobs.add(job)
				job.finish(self)
			else:
				self.running_jobs.remove(job)
				self.failed_jobs.add(job)
				self.error = job.exitstate
			self.job_lock.notify()

	def get_next(self):
		with self.job_lock:
			if len(self.ready_jobs) > 0:

				if self.error != 0:
					return None

				newjob = self.ready_jobs.pop()
				self.running_jobs.add(newjob)
				return newjob

			#TODO: could cause errors, investigate pls
			elif len(self.running_jobs) > 0 and len(self.pending_jobs) > 0:
				#if no jobs are ready, then remaining(pending) jobs are unlocked by currently running jobs
				#so the current worker has to wait here, until a job is ready, errors occur, or all jobs died.

				self._find_ready_jobs()
				self.job_lock.wait_for(self.nextjob_continue)

				if self.error != 0 or len(self.ready_jobs) == 0:
					return None

				newjob = self.ready_jobs.pop()
				self.running_jobs.add(newjob)
				return newjob

			else: #we are out of jobs!
				return None

	def nextjob_continue(self):
		'''return true, if:
		error occured
		out of jobs
		no more jobs running
		new job is ready
		'''
		return (self.error != 0 or self.running_jobs == 0 or len(self.ready_jobs) > 0 or len(self.pending_jobs) == 0)

	def _find_ready_jobs(self):
		'''find new jobs that are ready cause all their dependencies have been resolved'''
		with self.job_lock:
			new_ready_jobs = set(filter(lambda job: job.ready_to_build(), self.pending_jobs))
			self.pending_jobs -= new_ready_jobs
			self.ready_jobs |= new_ready_jobs

	def _create_workers(self):
		'''creates all BuildWorkers'''

		#delete the old workers from list, as they cannot be rerun.
		self.workers = []

		for i in range(self.max_workers):
			newworker = BuildWorker(self, i)
			self.workers.append(newworker)

	def _launch_workers(self):
		"""all worker threads are launched"""
		for worker in self.workers:
			worker.start()

	def run(self):
		"""launch the maximum number of concurrent jobs"""
		self._create_workers()
		self._launch_workers()

	def start(self):
		self.run()
#		threading.Thread(target=self.start).start()

	def join(self):
		"""wait here for all jobs to finish and generate a work summary"""
		for worker in self.workers:
			worker.join()
			print(repr(worker) + ": joined")

		if len(self.failed_jobs) > 0:
			print("==========\nFAILED jobs:")
			for job in self.failed_jobs:
				print(repr(job))

		if len(self.ready_jobs) > 0:
			print("++++++++++\njobs currently ready to build:")
			for job in self.ready_jobs:
				print(repr(job))

		if len(self.pending_jobs) > 0:
			#not all jobs have been built
			print("++++++++++\njobs blocked by dependencies:")
			for job in self.pending_jobs:
				print(repr(job))

		if len(self.finished_jobs) > 0:
			print("==========\njobs that have been built successfully:")
			for job in self.finished_jobs:
				print(repr(job))
		else:
			print("=========\n NO JOBS have been run successfully\n==========")

	def get_error(self):
		return self.error


class BuildOrder:
	'''A build order contains all targets that must be built'''

	def __init__(self):
		self.targets = set()
		self.filedict = dict()

	def set_thread_count(self, n = util.get_thread_count()):
		self.max_jobs = n

	def build_element_factory(self, filename):
		#TODO: actually this is a hacky dirt.
		if re.match(".*\\.(h|hpp)", filename):
			#print(filename + " generated HeaderFile")
			return self.find_create_header(filename)
		else:
			return SourceFile(filename)

	def find_create_header(self, fname):
		'''if not yet existing, this HeaderFile is created and returned'''
		rname = relpath(fname)

		if rname in self.filedict:
			print("reusing " + fname)
			return self.filedict[rname], True
		else:
			newfile = HeaderFile(fname)
			self.filedict[rname] = newfile
			return newfile, False

	def find_reuse_element(self, element):
		'''
		search for element duplicates
		return the duplicate, if found
		return the the original parameter element, if not found
		'''
		#strategy: find a candidate, then check whether the candidate equals
		#if matches: return the reused and True.

		encname = element.encname
		if encname in self.filedict:
			if element.equals(self.filedict[encname]):
				print("reusing " + repr(element))
				return (self.filedict[encname], True)

		#a new candidate is only stored, if it wasn't reused
		self.filedict[encname] = element
		return (element, False)

	def find_merge_element(self, element):
		'''
		search for element duplicates,
		return the ready-to-insert element eliminating dups
		'''

		elem_reused, reused = self.find_reuse_element(element)
		if reused:
			#maybe something needs to be merged..
			return elem_reused

		else:
			#maybe create some intelligent diff and inheritance
			return element

	def filedict_append(self, buildelement):
		key = buildelement.outname
		if key in self.filedict:
			self.filedict[key].append(buildelement)
		else:
			self.filedict[key] = [buildelement]


	def fill(self, confinfo, variables):
		'''
		fill this BuildOrder with contents for later processing

		attention: black magic is involved here.
		'''

		#---------------------
		#0. step: resolve usedby-requirements
		# move the file 'usedby' target definitions
		# into the target, so it 'uses' the source
		for source in variables["filelist"].get():
			for target in variables["usedby"].get(source):
				#TODO: we should not modify variables...
				#Add source filename to config(target).use:
				target_use = variables["use"].get(target)
				target_use.add(source)
				variables["use"].addv(target_use)

				#TODO: Add libs to config(target).libs ?


		#---------------------
		#1. step: create source-for-target configurations
		# create new Config object, with parents=[target,source]
		# and save it as confinfo[targetname + "-" + sourcename] = Config(...)
		# later, use .get(target + "-" + source) to access properties,
		# the get method will do the hyperresolution

		for target in variables["build"].get():
			for source in variables["use"].get(target):
				targetconf = confinfo[target]
				sourceconf = confinfo[source]
				newconf = conf.Config(parents=[targetconf,sourceconf], \
									  directory=sourceconf.directory, \
									  kind=conf.Config.SRCFORTARGET)
				confinfo[target + '-' + source] = newconf

		#---------------------
		#2. step: iterate through all dependencies and fill them
		#create BuildElements and fill them with information
		#supplied by the variables configuration

		for target in variables["build"].get():
			order_target = BuildTarget(target)

			for element in variables["use"].get(target):

				st = target + "-" + element

				#TODO: element may not be a source, but a ^/library.so.target
				#this happens when a target depends on another target
				#TODO: naming convention for this
				if element.endswith(".target"):
					order_target.depends_wanted.add(BuildTarget(element))
					continue

				else:
					order_file = SourceFile(source)

				crun = variables["c"].get(st)		#compiler
				crun += " " + variables["cflags"].get(st)	#compiler flags

				# encode the compiler flags etc
				objdir = variables["objdir"].get(st)

				#the encoded name: #TODO: maybe also encode the '/' in rsource
				encname = order_file.inname + "-" + generate_oname(crun)

				#assemble compiler output file without extension
				encpathname = relpath(objdir) + "/"
				encpathname += encname
				oname = encpathname + ".o"

				crun += " -c " + order_file.inname
				crun += " -o " + oname

				# add wanted (by config) dependency files (as smpath)
				file_depends = variables["depends"].get(st)
				#TODO: create object containers accordingly
				order_file.depends_wanted.union(file_depends)

				#add sourcefile path itself to depends
				ad = variables["autodepends"].get(st)

				if ad == "MD" or len(ad) == 0: # gcc MD enabled
					mdfile = encpathname + ".d"

					if os.path.isfile(mdfile):
						#if .d file exists:
						# add its contents as wanted dependencies
						for dep in parse_dfile(mdfile):
							dependency_header = HeaderFile(dep)

							out_tmp = dependency_header.outname
							order_file.depends_wanted.add(out_tmp)
							self.filedict[out_tmp] = dependency_header
					else:
						#if MD is enabled but not yet present:
						# we NEED to rebuild it
						order_file.needs_build = True
						print(mdfile + "will be generated")

						#see man 1 gcc (search for -MD)
					crun += " -MD"  # (re)generate c headers dependency file

				elif ad == "no":
					pass
				else:
					#let's not ignore an unknown autodetection mode bwahaha
					raise Exception(element + ": unknow autodetection mode: " + ad)

				order_file.loglevel = variables["loglevel"].get(st)
				order_file.crun = crun
				order_file.encname = encname
				order_file.outname = oname

				s_prb = variables["prebuild"].get(st)
				if len(s_prb) > 0:
					order_file.prebuild = s_prb

				s_pob = variables["postbuild"].get(st)
				if len(s_pob) > 0:
					order_file.postbuild = s_pob

				order_target.depends_wanted.add(order_file)

			# <- for each target loop
			order_target.loglevel = variables["loglevel"].get(target)
			ctrun = variables["c"].get(target)		#compiler for TARGET
			ctrun += " " + variables["cflags"].get(target)	#compiler flags
			ctrun += " " + variables["ldflags"].get(target)	#link flags
			ctrun += " -o " + relpath(target)		#target output name

			t_prb = variables["prebuild"].get(target)
			if len(s_prb) > 0:
				order_target.prebuild = t_prb

			t_pob = variables["postbuild"].get(target)
			if len(t_pob) > 0:
				order_target.postbuild = t_pob

			target_depends = variables["depends"].get(target)
			order_target.depends_wanted.union(target_depends)

			#append all object files for linkage
			#TODO: rewrite and relocate to somewhere else!
			for ofile in order_target.depends_wanted:
				ctrun += " " + relpath(ofile.outname)

			order_target.crun = ctrun

			#if another target depends on this one, we need that:
			self.filedict[order_target.outname] = order_target

			#include current target to the build order:
			self.targets.add(order_target)

		#----------------------
		# 3. step: reuse wanted dependencies to add buildelements
		# to the correct hierarchy etc

		#TODO: this method does not respect all tests of BuildElement.equals
		#e.g. it wil be a giant pile of crap with different pre/postbuilds

		for order_target in self.targets:

			for target_dependency in order_target.depends_wanted:
				#search the dependency and if exists, add it to the target file

				if type(target_dependency) == BuildTarget:
					final_t_dep = self.find_merge_element(target_dependency)
					order_target
				else: #sourcefile
					final_dep = self.find_merge_element(target_dependency)
					order_target.add_dependency(final_dep)


			#TODO: a target can be dependent on e.g. a library.
			#for dep in target_depends:
			#	d, _  = self.build_element_factory(dep)
			#	order_target.add_dependency(d)

		#<- direct function level here

	def __str__(self):
		out = "\n\n%%%%%%%%%%%%%%%%%\n BUILD ORDER"
		for t in self.targets:
			out += str(t)
		out += "\n%%%%%%%%%%%%%%%%%\n"
		return out

	def text(self):
		out = "===== BuildOrder " + str(id(self)) + " has " + str(len(self.targets)) + " targets.\n"

		n = 0
		for t in self.targets:
			out += "target " + str(n) + ":\n" + t.text() + "\n"
			n = n+1
		out += "===== End BuildOrder\n"
		return out

	def makefile(self):
		'''generate a GNU Makefile for this BuildOrder, then has the same functionality as Builder.build(order)'''
		#TODO
		pass

	def graphviz(self):
		'''neat graph representation of the dependencies'''
		#TODO http://linux.die.net/man/1/graph-easy
		pass

	def ascii(self):
		#TODO: maybe even something text-only -> awesome build overview.
		pass

	def __repr__(self):
		ret = "BuildOrder: [ "
		for t in order.targets:
			ret += t.name + " "
		ret += "]"
		return ret



class BuildElement:

	def __init__(self, name):
		self.depends = set()
		self.depends_wanted = set()
		self.depends_finished = set()
		self.name = smpath(name)
		self.inname = relpath(name)
		self.outname = ""
		self.encname = ""
		self.crun = ""
		self.prebuild = ""
		self.postbuild = ""
		# does this file need to be rebuilt:
		self.needs_build = False
		self.ready = False
		# the parent BuildElements, which are blocked by this one:
		self.blocks = set()
		self.worker = None
		self.loglevel = 2	# standard value?
		self.exitstate = 0
		self.finished = False
		self.realfile = False
		#TODO: store file mtime

	def run(self):
		raise NotImplementedError("Implement this shit for a working compilation...")

	def equals(self, other):
		print(repr(self) + " equal test")

		if id(self) == id(other):
			return True

		if not type(other) == type(self):
			return False

		if not self.encname == other.encname:
			return False

		if not self.prebuild == other.prebuild:
			return False

		if not self.postbuild == other.postbuild:
			return False

		if not len(self.depends) == len(other.depends):
			return False

		if not self.depends == other.depends:
			return False

		print(repr(self) + '(' + str(id(self)) + ')' + " is equal to " + repr(other) + '(' + str(id(other)) + ')')
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
		print(repr(self) + " -> adding dependency " + repr(newone))
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

	def check_needs_build(self):
		'''
		set self.needs_build to the correct value
		should be overridden if appropriate (e.g. header file)
		'''

		if os.path.isfile(self.outname):
			if os.path.getmtime(self.outname) < os.path.getmtime(self.inname):
				self.needs_build = True
				return True
			else:
				self.needs_build = False

		else: # outname does not exist
			self.needs_build = True
			return True

		#only check dependencies, if we don't need a build (we'd have returned then)
		for d in self.depends:
			try:
				# check for modification times
				print("checking mtime of -> " + repr(d))
				#TODO: use dict of mtimes
				if os.path.getmtime(fl) > os.path.getmtime(self.outname):
					self.needs_build = True
					print("==> Build needed: " + repr(d) + " is newer than " + self.outname)
					break

			except OSError as e:
				print(str(e) + " -> Ignoring for now.")

		self.finished = not self.needs_build
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



class HeaderFile(BuildElement):
	"""headerfile for a source file, never needs to be built"""

	def __init__(self, hname):
		BuildElement.__init__(self, hname)
		self.outname = self.inname

	def check_needs_build(self):
		self.needs_build = False
		return False

	def run(self):
		return Exception("HeaderFiles should never be run. skip them.")
		#print("[" + self.worker.num + "]: " + repr(self))

	def __repr__(self):
		return self.inname


class SourceFile(BuildElement):
	"""a source file that is compiled to an object file"""

	def __init__(self, filename):
		BuildElement.__init__(self, filename)

	def run(self):
		'''this method compiles a the file into a single object.'''

		ret = 0

		if self.prebuild:
			print(repr(self.worker) + ": prebuild for " + repr(self) + " '" + self.prebuild + "'")
			#TODO: redirect the output if we get a global logger
			#ret = os.system(self.prebuild)

		if ret != 0:
			failat = "prebuilding"
		else:
			print(repr(self.worker) + ": == building -> " + repr(self))

			## compiler is launched here
			#TODO: correct invocation
			print(repr(self.worker) + ": EXEC:: " + self.crun)
			#ret = subprocess.call(shlex.split(self.crun), shell=False)
			time.sleep(1)

			print(repr(self.worker) + ": == done building -> " + repr(self))

		#ret = random.choice([0,0,0,0,1,8])

		if ret != 0:
			failat = "compiling"
		else:
			if self.postbuild:
				print(repr(self.worker) + ": postbuild for " + repr(self) + " '" + self.postbuild + "'")
				#TODO: also redirecto output stream
				#ret = os.system(self.postbuild)
			if ret != 0:
				failat = "postbuilding"

		if ret > 0:
			print(repr(self.worker) + ": " + repr(self) + " Error " + str(ret) + " " + failat  + " ===============")
			self.exitstate = ret
		else:
			self.exitstate = 0

	def __repr__(self):
		return self.inname

	def __str__(self):
		return self.text()


class BuildTarget(BuildElement):
	'''A build target has a list of all files that will be linked in the target'''

	def __init__(self, tname):
		BuildElement.__init__(self, tname)
		self.name = tname
		self.outname = relpath(tname) #TODO: respect suffix variables (.target)
		self.encname = generate_oname(self.outname)
		self.inname = None #target's inname cannot be used

	def run(self):
		'''this method compiles a single target.'''

		ret = 0		#return value storage

		if self.prebuild:
			print("prebuild for " + repr(self) + " '" + self.prebuild + "'")
			#ret = os.system(self.prebuild)

		if ret != 0:
			failat = "prebuilding"
		else:
			print(repr(self.worker) + ": == linking -> " + repr(self))

			## compiler is launched here
			#TODO: correct invocation
			print(repr(self.worker) + ": EXEC:: " + self.crun)
			#ret = subprocess.call(shlex.split(self.crun), shell=False)
			time.sleep(1)

			print(repr(self.worker) + ": == done linking -> " + repr(self))

		#ret = random.choice([0,0,1])

		if ret != 0:
			failat = "linking"
		else:
			if self.postbuild:
				print("postbuild for " + repr(self) + " '" + self.postbuild + "'")
				#ret = os.system(self.postbuild)

			if ret != 0:
				failat = "postbuilding"

		if ret > 0:
			fail = True
		else:
			fail = False

		if fail:
			print(repr(self.worker) + ": " + repr(self) + " Error " + str(ret) + " " + failat  + " ===============")
			self.exitstate = ret
		else:
			self.exitstate = 0

	def __str__(self):
		return self.text()

	def __repr__(self):
		return self.outname


def parse_dfile(filename):
	'''parse a gcc .d file and return a list of dependency header filenames'''
	try:
		with open(filename, 'r') as f:
			content = f.readlines() #list of line, including a trailing \\n (sic)
			content = [ list(clean_dfile_line(l)) for l in content ]
			dependencies = []
			for part in content: # concat all lists
				dependencies += part

			return dependencies
	except IOError as e:
		print(str(e) + " -> parsing dependency header failed")

		#TODO: really ignore?
		return [];

def clean_dfile_line(line):
	'''converts a .dfile line to a list of header dependencies'''
	#TODO: will need testing
	hmatch = re.compile(r"[-\w/\.]+\.(h|hpp)") #matches a single header file
	parts = re.split(r"\s+", line)

	#return all matching header files as list
	return filter(lambda part: hmatch.match(part), parts)
#	return [ part for part in parts if hmatch.match(part) ]



def main():
	print("fak u dolan")
	order = BuildOrder()

	#confinfo and variables are fucking global
	#but now we catch those fuckers and never use them as global again..
	order.fill(confinfo, variables)
	print("\n")
	pprint.pprint(order.filedict)
	print("\n")

	m = JobManager()
	m.queue_order(order)

	print(order.text())

#	m.start()
#	m.join()

	#show status after the build
#	print(order.text())

	#after all targets:
	if m.get_error() == 0:
		print("sftmake builder shutting down regularly")
	else:
		print("sftmake builder exiting due to error")


if __name__ == "__main__":
	main()
