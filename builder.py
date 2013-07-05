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
from util import abspath,smpath,relpath,generate_oname
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
	def __init__(self, name=""):
		self.l = dict()
		self.n = name

	def get(self, param):
		print("getting [" + param + "] @" + self.n + " = ", end='')
		ret = self.l[param]
		print(str(ret))
		return ret

	def setv(self, key, val):
		print("setting [" + key + "] @" + self.n + " = " + str(val))
		self.l[key] = val

	def pushv(self, key, val):
		print("pushing [" + key + "] @" + self.n + " = " + str(val))
		if key in self.l:
			self.l[key].append(val)
		else:
			self.l[key] = [val]
	def __repr__(self):
		return "vartestadvanced (" + str(id(self)) + ") :\t" + pprint.pformat(self.l, width=300)


#test purpose only
variables = dict()
variables["c"] = vartest("gcc")
variables["build"] = vartest({"^/lolbinary", "^/liblol.so"})
variables["filelist"] = vartest({'^/main.c', '^/both.c', '^/library0.c', '^/library1.c'})

variables["objdir"] = vartest("^/.objdir")

variables["use"] = vartestadv(name="use")
variables["usedby"] = vartestadv(name="usedby")
variables["depends"] = vartestadv(name="depends")
variables["ldflags"] = vartestadv("ldflags")
variables["cflags"] = vartestadv("cflags")

variables["cflags"].setv("^/lolbinary", "-O1 -march=native")
variables["cflags"].setv("^/lolbinary-^/main.c", "-O1 -march=native")
variables["cflags"].setv("^/lolbinary-^/both.c", "-O1 -march=native")
variables["cflags"].setv("^/liblol.so", "-O1 -march=native -fPIC")
variables["cflags"].setv("^/liblol.so-^/library0.c", "-O1 -march=native -fPIC")
variables["cflags"].setv("^/liblol.so-^/library1.c", "-O1 -march=native -fPIC")
variables["cflags"].setv("^/liblol.so-^/both.c", "-O1 -march=native -fPIC")


variables["ldflags"].setv("^/liblol.so", "-shared -Wl,-soname,liblol.so")
variables["ldflags"].setv("^/lolbinary", "-L. -llol")

variables["depends"].setv("^/main.c", {"^/both.c"})#set())
variables["depends"].setv("^/both.c", set())
variables["depends"].setv("^/library0.c", set())
variables["depends"].setv("^/library1.c", set())
variables["depends"].setv("^/lolbinary", {"^/liblol.so"})
variables["depends"].setv("^/liblol.so", set())

variables["depends"].setv("^/liblol.so-^/both.c", set())
variables["depends"].setv("^/liblol.so-^/library0.c", set())
variables["depends"].setv("^/liblol.so-^/library1.c", set())
variables["depends"].setv("^/lolbinary-^/main.c", set())
variables["depends"].setv("^/lolbinary-^/both.c", set())

variables["use"].setv("^/lolbinary", {'^/both.c', '^/main.c'})
variables["use"].setv("^/liblol.so", {'^/both.c', '^/library0.c', '^/library1.c'})
variables["usedby"].setv("^/main.c", set())
variables["usedby"].setv("^/both.c", set())
variables["usedby"].setv("^/library0.c", set())
variables["usedby"].setv("^/library1.c", set())

variables["autodepends"] = vartest("MD") #vartest("no")
variables["prebuild"] = vartest("echo startin build")
variables["postbuild"] = vartest("echo finished build")
variables["loglevel"] = vartest("2")

print("var initialisation: \n")
pprint.pprint(variables)
print("\n\n\n")


confinfo = {}
conf_base = conf.Config('^', conf.Config.TYPE_DIR, [], '^')
conf_main = conf.Config('^/main.c', conf.Config.TYPE_SRC, [conf_base], '^')
conf_lib0 = conf.Config('^/library0.c', conf.Config.TYPE_SRC, [conf_base], '^')
conf_lib1 = conf.Config('^/library1.c', conf.Config.TYPE_SRC, [conf_base], '^')
conf_both = conf.Config('^/both.c', conf.Config.TYPE_SRC, [conf_base], '^')
conf_lib = conf.Config('^/liblol.so', conf.Config.TYPE_TARGET, [conf_base], '^')
conf_bin = conf.Config('^/lolbinary', conf.Config.TYPE_TARGET, [conf_base], '^')
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
variables["c"].setval([Val("g++", None, Val.MODE_APPEND)], "^/folder/file.c")
"""

#TODO: output queue, fixing thread interferences with msgs containing newlines

#TODO: unit test class

#TODO: add more shell commands, e.g. all dependencies ready

#TODD: option for MD to only check for file in ^/ (exclude system headers)

class BuildWorker:
	"""A worker thread that works and behaves like a slave. Be careful, it bites."""

	def __init__(self, manager, num=-1):
		self.thread = threading.Thread(target=self.run)
		self.manager = manager
		self.num = num
		self.job = None   #The BuildElement currently being processed by this worker

	def run(self):
		print("" + repr(self) + ": started")
		while True:
			self.job = self.manager.get_next(self)
			if self.job == None:
				#no more jobs available
				#so the worker can die!
				with self.manager.job_lock:
					self.manager.job_lock.notify()
				break

			self.wprint("fetched job ->\t" + repr(self.job))
			self.job.worker = self

			if self.job.check_needs_build():
				#TODO: same output colors for each worker
				self.wprint("making job ->\t" + repr(self.job))
				self.job.run()
			else:
				self.wprint("skipped job ->\t" + repr(self.job))

			self.manager.finished(self.job)
		self.wprint("dead")

	def start(self):
		self.thread.start()

	def join(self):
		self.thread.join()

	def wprint(self, msg):
		print(repr(self) + ": " + msg)

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
		self.filesys_lock = threading.Condition()

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

	def get_next(self, worker):
		try:
			with self.job_lock:
				#print(repr(worker) + " get_next running:"+str(len(self.running_jobs))+" ready:"+str(len(self.ready_jobs))+" pending:"+str(len(self.pending_jobs)))
				if len(self.ready_jobs) > 0:
					#jobs are ready to process

					if self.error != 0:
						return None

					newjob = self.ready_jobs.pop()
					self.running_jobs.add(newjob)
					return newjob

				elif len(self.running_jobs) > 0 and len(self.pending_jobs) > 0:
					#if no jobs are ready:
					# then remaining(pending) jobs are unlocked
					# by currently running jobs

					#so the worker that wants to get a new job
					#has to wait here, until a new job is ready,
					#an errors occur, all jobs died, or no more jobs
					#are pending.

					self.job_lock.wait_for(self.nextjob_continue)

					if self.error != 0 or len(self.ready_jobs) == 0:
						#the running jobs failed
						#or did not unlock a pending job
						return None

					newjob = self.ready_jobs.pop()
					self.running_jobs.add(newjob)
					return newjob

				else:
					#we are out of jobs!
					return None

		except KeyboardInterrupt:
			#maybe catch useful exceptions here
			pass

	def nextjob_continue(self):
		'''
		can a waiting worker continue to fetch work or die?
		if not, then it will wait another round until waked up again.

		return true, if:
		error occured
		out of jobs
		no more jobs running
		new job is ready
		'''

		result = False
		result |= self.error != 0
		result |= len(self.running_jobs) == 0
		result |= len(self.ready_jobs) > 0
		result |= len(self.pending_jobs) == 0

		return result

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

	def join(self):
		"""wait here for all jobs to finish and generate a work summary"""
		for worker in self.workers:
			worker.join()
			print(repr(worker) + ": joined")

		self.dump_jobtable()

	def dump_jobtable(self):
		if len(self.failed_jobs) > 0:
			print("==========\nFAILED jobs:")
			for job in self.failed_jobs:
				print(repr(job))

		if len(self.running_jobs) > 0:
			print("++++++++++\njobs currently running:")
			for job in self.running_jobs:
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
		self.usedelements = set()

	def set_thread_count(self, n = util.get_thread_count()):
		self.max_jobs = n

	def find_reuse_element(self, element):
		'''
		search for element duplicates
		return the duplicate, if found
		return the the original parameter element, if not found
		'''
		#strategy: find a key and get it's candidates,
		#then check whether one of these candidates .equals()
		#if matches: return the reused and True.

		print("finding reusage for " + repr(element) + " (" + str(type(element))+ ")")

		#key to determine candidates, set it in filedict_append!!
		key = element.outname
		if key in self.filedict:
			for candidate in self.filedict[key]:
				print("for " + repr(element) + " try candidate " + repr(candidate))

				#this order is important, element may have a custom .equals implementation
				if element.equals(candidate):
					print("reusing " + repr(candidate) + " (" + str(type(candidate))+ ") for " + repr(element) )
					return (candidate, True)
		else:
			print("no reusage candidate found for outname [" + key + "] in filedict")

		if type(element) == WantedDependency:
			raise Exception("wanted dependency of (TODO) not found: " + repr(element))

		#a new candidate is only stored, if it wasn't reused
		#so the equal element (which was reused) is dropped
		self.filedict_append(element)
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
		'''
		"bucket-hashing" for reusable candidates
		the "hash" is the element.outname
		'''

		#set this in find_reuse_element as well!!!
		key = buildelement.outname

		if key in self.filedict:
			self.filedict[key].append(buildelement)
		else:
			self.filedict[key] = [buildelement]


	def fill(self, confinfo, variables):
		'''
		fill this BuildOrder with contents for later processing

		configuration inheritance and configuration variable dict
		are used to create all the buildelements with their configuration
		specified by the user in the variables array

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
				variables["use"].setv(target_use)

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
				newconf = conf.Config(name="TODO", parents=[targetconf,sourceconf], directory=sourceconf.directory, conftype=conf.Config.TYPE_SRCFORTARGET)
				confinfo[target + '-' + source] = newconf

		#---------------------
		#2. step: iterate through all dependencies and fill them
		#create BuildElements and fill them with information
		#supplied by the variables configuration

		for target in variables["build"].get():
			order_target = BuildTarget(target)

			for element in variables["use"].get(target):

				st = target + "-" + element

				#this object will now be filled with information
				order_file = SourceFile(element)

				crun = variables["c"].get(st)		#compiler
				crun += " " + variables["cflags"].get(st)	#compiler flags

				# encode the compiler flags etc
				objdir = relpath(variables["objdir"].get(st))

				#the encoded name: #TODO: maybe also encode the '/' in rsource
				encname = order_file.inname + "-" + generate_oname(crun)

				#assemble compiler output file without extension
				encpathname = objdir + "/"
				encpathname += encname
				oname = encpathname + ".o"

				crun += " -c " + order_file.inname
				crun += " -o " + oname

				# add wanted (by config) dependency files
				file_depends = variables["depends"].get(st)
				for d in file_depends:
					d_obj = WantedDependency(d)
					order_file.depends_wanted.add(d_obj)

				#add sourcefile path itself to depends
				ad = variables["autodepends"].get(st)

				if md_enabled(ad): # if gcc MD enabled
					mdfile = encpathname + ".d"

					order_file.mdfile = mdfile

					if os.path.isfile(mdfile):
						#if .d file exists:
						# add its contents as wanted dependencies
						for dep in parse_dfile(mdfile):
							dep_header = HeaderFile(dep)

							#TODO: ignore system headers variable
							if False and dep_header.headertype == HeaderFile.systemheader:
								pass
							else:
								final_header = self.find_merge_element(dep_header)
								order_file.add_dependency(final_header)

					else:
						#if MD is enabled but not yet present:
						# we NEED to rebuild this source
						order_file.needs_build = True
						print(mdfile + " will be generated")

						#see man 1 gcc (search for -MD)
					crun += " -MD"  # (re)generate c headers dependency file


				order_file.loglevel = variables["loglevel"].get(st)
				order_file.crun = crun
				order_file.encname = encname
				order_file.outname = oname
				order_file.objdir = objdir

				s_prb = variables["prebuild"].get(st)
				if len(s_prb) > 0:
					order_file.prebuild = s_prb

				s_pob = variables["postbuild"].get(st)
				if len(s_pob) > 0:
					order_file.postbuild = s_pob

				order_target.depends_wanted.add(order_file)
				self.filedict_append(order_file)

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

			#create wanted dependencies (by config) for this target.
			target_depends = variables["depends"].get(target)
			pprint.pprint(target_depends)
			for d in target_depends:
				d_obj = WantedDependency(d)
				order_target.depends_wanted.add(d_obj)

			#append all object files for linkage
			#TODO: rewrite and relocate to somewhere else!
			for ofile in order_target.depends_wanted:
				#add all outnames of all dependency sourcefiles
				#to the compiler cmd line
				if type(ofile) == SourceFile:
					ctrun += " " + relpath(ofile.outname)
				else:
					continue

			order_target.crun = ctrun

			#if another target depends on this one, we need that:
			self.filedict_append(order_target)

			#include current target to the build order:
			self.targets.add(order_target)

		#----------------------
		# 3. step: reuse wanted dependencies to add buildelements
		# to the correct hierarchy etc

		print("\ncurrent filedict:")
		pprint.pprint(self.filedict)

		print("\ninserting and reusing dependencies:")
		for target in self.targets:
			for wanted_dependency in target.depends_wanted:
				print("-" + repr(wanted_dependency) + " " + str(type(wanted_dependency)) + " wanted for " + repr(target))
				final_dep = self.find_merge_element(wanted_dependency)
				print("-using " + str(id(final_dep)) + "(" + str(type(final_dep))  + ")")
				target.add_dependency(final_dep)

		#<- direct function level here

	def __str__(self):
		return self.text()

	def text(self):
		out = "===== BuildOrder " + str(id(self)) + " has " + str(len(self.targets)) + " targets.\n"

		n = 0
		for t in self.targets:
			out += "target " + str(n) + ":\n" + t.text() + "\n"
			n = n+1
		out += "===== End BuildOrder\n"
		return out

	def makefile(self):
		'''
		generate a GNU Makefile for this BuildOrder, which
		then has the same functionality as Builder.build(order)
		means: represent dependencies as real Makefile
		'''

		out =  "# Makefile representation of BuildOrder\n"
		out += "# [SFT]make version $version\n\n"

		lines = set()  #all rule lines for the makefile
		nonblocking = set() #elements that don't block others

		#these are all files to be built in this order:
		all_files = self.as_set()

		#filter all_files for nonblocking ones and headers
		for element in all_files:
			if len(element.blocks) == 0:
				nonblocking.add(element)

			#don't create a rule for a makefile with no dependencies
			if not isinstance(element, HeaderFile) or len(element.depends) > 0:
				lines.add(element)

		#create make rule 'all' that will be the default when running 'make'
		#all nonblocking elements (-> targets) are added.
		out += "all:"
		for nb in nonblocking:
			out += " " + nb.outname

		objdirs = set()
		out += "\n\n"

		#make clean rule, just all outnames
		out += "clean:"
		out += "\n\t#delete all objects and target files:"

		out += "\n\trm -f"
		for element in lines:
			if isinstance(element, SourceFile):
				if element.objdir:
					objdirs.add(element.objdir)
				if element.mdfile:
					out += " " + element.mdfile

			out += " " + element.outname

		#for make clean, also remove the objdir if it exists (and is empty)
		out += "\n\t#delete all object directories as well:"

		for objdir in objdirs:
			out += "\n\tif [ -d " + objdir + " ]; then rmdir -p " + objdir + "; fi"

		out += "\n\n"

		#create make rules for all the elements, rulename is their outname
		for element in lines:
			out += "# " + element.name + " (" + str(type(element)) + ")\n"

			#set rule name:
			out += element.outname + ":"

			#add dependencies of this rule:
			for d in (element.depends | element.depends_finished):
				out += " " + d.outname

			#ensure creation of element's objdir:
			if isinstance(element, SourceFile) and element.objdir:
				out += "\n\t@mkdir -p " + element.objdir

			#execute prebuild:
			if element.prebuild:
				out += "\n\t" + element.prebuild

			#the main compiler invokation for this file:
			out += "\n\t" + element.crun

			#execute postbuild:
			if element.postbuild:
				out += "\n\t" + element.postbuild

			out += "\n\n"

		#add phony target (-> execute always) for rule 'all' and 'clean'
		out += ".PHONY: all clean"
		out += "\n\n"

		return out


	#TODO: implement option for filtering out system headers
	def graphviz(self):
		'''
		neat graph representation of the dependencies

		this function generates a dot file for graphviz
		render a png, pdf or whatever using dot (or other graphwiz tools
		'''

		#dot file header:
		out = "digraph \"sftmake dependencies for $projectname(TODO)\" {\n"
		out += "overlap=scale\n"
		out += "splines=true\n"
		out += "sep=.1\n"
		out += "node [style=filled]\n"

		#for graph drawing, store all edges:
		#key = originating node id
		#value = [list of it's dependencies ids]
		edges = dict()

		all_files = self.as_set()

		#iterate over all single elements of the dependency tree
		for element in all_files:
			elid = id(element)


			#determine the color of the current node
			if type(element) == BuildTarget:
				color = "red"

			elif type(element) == SourceFile:
				color = "green"

			elif type(element) == HeaderFile:
				if element.headertype == HeaderFile.projectheader:
					color = "lightblue"
				else:
					color = "lightyellow"

					#TODO: filter out system headers if wanted
					filtersysheaders = False
					if filtersysheaders:
						continue

			#maybe set color by rgb values in the future:
			#color = cr + ',' + cg + ',' + cb

			nout = '// ' + repr(element) + '\n'
			nout += '"' + str( id(element) )  + '" '
			nout += '[fillcolor="' + color + '",'
			nout += 'label="' + repr(element) + '"]\n'

			#add the new node to the output file
			out += nout

			#add dependency arrows to the edge list:
			for dep in (element.depends | element.depends_finished):
				#element is dependent on dep, so add dep --> elem
				#as one element has multiple dependencies,
				#multiple --> must be drawn from multiple dependencies
				#=> edges[element] = [list of its dependencies]

				depid = id(dep)

				if elid in edges:
					edges[ elid ].add( depid )
				else:
					edges[ elid ] = { depid }


		#as all nodes have been created, add the directed edges now:
		out += "\n// edge list: \n"

		#iterate over all nodes and add arrows originating from them
		for elemk in edges.keys():
			elem = edges[elemk]
			out += '{ '

			#for each dependency (id) that elem the current has:
			for dep in elem:
				out += '"' + str(dep) + '" '

			out += '} -> "' + str(elemk) + '"\n'


		out += "}"

		#that's it, return the dot text:
		return out

	def ascii(self):
		#http://linux.die.net/man/1/graph-easy
		#TODO: maybe even something text-only -> awesome build overview.
		pass

	def as_set(self):
		'''
		return all buildelements of this order as a set.
		'''

		visited = set()
		def recursenodes(element):
			visited.add(element)
			for dep in (element.depends | element.depends_finished):
				if not dep in visited:
					recursenodes(dep)

		for target in self.targets:
			recursenodes(target)

		return visited

	def cleanup_file_list(self):
		'''
		returns (filenames cleanable, directories cleanable)
		'''
		allfiles = self.as_set()
		todelete = filter(lambda elem: not isinstance(elem, HeaderFile), allfiles)

		del_filenames = set()
		del_directories = set()
		for el in todelete:
			del_filenames.add(el.outname)
			if isinstance(el, SourceFile):
				if el.objdir:
					del_directories.add(el.objdir)
				if el.mdfile:
					del_filenames.add(el.mdfile)

		return (del_filenames, del_directories)

	def cleanup_outfiles(self):
		'''
		delete all files produced by build
		this should be the make clean functionality
		'''

		del_filenames, del_directories = self.cleanup_file_list()

		for f in del_filenames:
			if os.path.isfile(f):
				print("cleanup: deleting file " + f)
				os.remove(f)
			else:
				print("cleanup: file not existing, skipping: " + f)

		for d in del_directories:
			if os.path.isdir(d):
				print("cleanup: deleting directory " + d)
				os.rmdir(d)
			else:
				print("cleanup: directory not existing, skipping: " + d)

	def __repr__(self):
		ret = "BuildOrder: [ "
		for t in self.targets:
			ret += repr(t) + " "
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

		ret = 0		#return value storage

		if elem_type == 0: #target
			action = "linking"
		elif elem_type == 1: #sourcefile
			action = "compiling"
			with self.worker.manager.filesys_lock:
				dirname = os.path.dirname(self.outname)
				if not os.path.exists(dirname):
					self.worker.wprint("creating output directory '" + dirname + "'")
					os.mkdir(dirname)
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
			self.worker.wprint(repr(self) + " Error " + str(ret) + " " + failat  + " ===============")
			self.exitstate = ret
		else:
			self.exitstate = 0

	def equals(self, other):
		#TODO: print, what test failed
		#print(repr(self) + " equal test == " + repr(other))

		if id(self) == id(other):
			return True

		if not type(other) == type(self):
			print("type check failed")
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
		set self.needs_build to the correct value
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
					raise Exception("requested " + repr(self) + ".inname does not exist")

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

		print(repr(self) + " testing with " + repr(other))

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

		if util.in_smdir(self.inname):
			self.headertype = HeaderFile.projectheader
			self.outname = self.inname
		else:
			self.headertype = HeaderFile.externalheader
			self.outname = abspath(self.inname)

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
		return space + self.outname + "\n"

	def run(self):
		return Exception("HeaderFiles should never be run. skip them.")

	def __repr__(self):
		return self.outname


class SourceFile(BuildElement):
	"""a source file like lolmysource.c"""

	def __init__(self, filename):
		super().__init__(filename)
		self.objdir = ""
		self.mdfile = ""


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


def parse_dfile(filename):
	'''parse a gcc -MD .d file and return a list of dependency header filenames'''
	try:
		with open(filename, 'r') as f:
			content = f.readlines() #list of line, including a trailing \\n (sic)
			dependencies = list()
			for l in content:
				dependencies += clean_dfile_line(l)

			return dependencies
	except IOError as e:
		raise Exception(str(e) + " -> parsing dependency header failed")


def clean_dfile_line(line):
	'''converts a .dfile line to a list of header dependencies'''
	hmatch = re.compile(r"[-\w/\.]+\.(h|hpp)") #matches a single header file
	parts = re.split(r"\s+", line)

	#return all matching header files as list
	return filter(lambda part: hmatch.match(part), parts)
#	return [ part for part in parts if hmatch.match(part) ]

def md_enabled(ad):
	'''option interpreter, is gcc -MD enabled?'''

	if ad == "MD" or len(ad) == 0:
		return True
	elif ad == "no" or ad == "disable" or ad == "nope":
		return False
	else:
		raise Exception(repr(element) + ": unknow autodetection mode: '" + ad + "'")


def main():
	print("fak u dolan")
	order = BuildOrder()

	#confinfo and variables are fucking global
	#but now we catch those fuckers and never use them as global again..
	order.fill(confinfo, variables)
	print("\n")
	pprint.pprint(order.filedict)
	print("\n")

	m = JobManager(4)
	m.queue_order(order)

	dotfile = open("/tmp/sftmake.dot", "w")
	dotfile.write(order.graphviz())

	makefile = open("/tmp/sftmake.makefile", "w")
	makefile.write(order.makefile())

	#print(order.text())

	m.start()
	m.join()

	#show status after the build
	#print(order.text())

	#after all targets:
	if m.get_error() == 0:
		print("sftmake builder shutting down regularly")
	else:
		print("sftmake builder exiting due to error")


if __name__ == "__main__":
	main()
