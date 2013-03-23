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

import base64
import multiprocessing
import os.path
import pprint
import random
import re
import shlex
import subprocess
import threading
import time


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
	def __init__(self):
		self.l = dict()

	def get(self, param):
		ret = self.l[param]
		print("getting [" + param + "]: " + str(ret))
		return ret

	def addv(self, key, val):
		self.l[key] = val

	def __repr__(self):
		return "vartestadvanced:\t" + pprint.pformat(self.l, width=300)

try:
	smpath("/tmp/a")
except NameError:
	from util import smpath
#	print("redefining smpath() as stub")
#	def smpath(path):
#		'''stub for testing'''
#		return path

try:
	relpath("^/a")
except NameError:
	from util import relpath
#	print("redefining relpath() as stub")
#	def relpath(path):
#		'''stub for testing'''
#		return path

try:
	generate_oname("gschicht")
except NameError:
	from util import generate_oname
#	print("redefining generate_oname() as stub")
#	def generate_oname(name):
#		encoded = base64.b64encode(bytearray(name, 'utf-8'))
#		return encoded.decode('utf-8')


#test purpose only
variables = {}
variables["c"] = vartest("gcc")
variables["build"] = vartest(["^/lolbinary", "^/liblol.so"])
variables["cflags"] = vartest("-O1 -march=native")
variables["ldflags"] = vartest("-L. -llol")
variables["objdir"] = vartest("^/.objdir")

variables["use"] = vartestadv()
variables["depends"] = vartestadv()
variables["depends"].addv("^/main.c", [])
variables["depends"].addv("^/both.c", [])
variables["depends"].addv("^/library0.c", [])
variables["depends"].addv("^/library1.c", [])
variables["depends"].addv("^/lolbinary", ["^/liblol.so"])
variables["depends"].addv("^/liblol.so", [])
variables["use"].addv("^/lolbinary", ['^/both.c', '^/main.c'])
variables["use"].addv("^/liblol.so", ['^/both.c', '^/library0.c', '^/library1.c'])

variables["autodepends"] = vartest("MD")
variables["prebuild"] = vartest("echo startin build")
variables["postbuild"] = vartest("echo finished build")
variables["loglevel"] = vartest("2")

print("var initialisation: \n")
pprint.pprint(variables)
print("\n\n\n")



#TODO: when buildelements are used by multiple parents, detect that (e.g. header files) (respecting the differing variable values!)
#This means: extend the current tree model of dependencies to a graph model.

#TODO: colored output

#TODO: output queue, fixing thread interferences with msgs containing newlines

#TODO: unit test class

#TODO: pre/postrun must not be inherited, only if explicitly specified

#TODO: add more shell commands, e.g. all dependencies ready

#TODO: add testing features and bisect support


#output_lock = threading.Condition()

def get_thread_count():
	"""gets the number or hardware threads, or 1 if that can't be done"""

	try:
		return multiprocessing.cpu_count()
	except NotImplementedError: # may happen under !POSIX
		fallback = 1
		sys.stderr.write('warning: cpu number detection failed, fallback to ' + fallback + '\n')
		return fallback;



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

	def __init__(self, max_workers=get_thread_count()):
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

	def set_thread_count(self, n = get_thread_count()):
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

	def find_reuse_source(self, sourcefile):
		'''if not yet existng, a SourceFile is created and returned'''

		encname = sourcefile.encname
		if encname in self.filedict:
			if sourcefile.equals(self.filedict[encname]):
				print("reusing " + repr(sourcefile))
				return self.filedict[encname], True

		self.filedict[sourcefile.encname] = sourcefile
		return sourcefile, False


	def fill(self, conf):
		'''
		fill this BuildOrder with contents for later processing

		attention: black magic is involved here.
		'''


		#---------------------
		#0. step: create source-for-target configurations
		#TODO: merge target and source configuration -> source-for-target
		# and save it as variables[targetname + "-" + sourcename]
		# for all file properties, use .get(target + "-" + source) to access properties
		#TODO: respect prebuild/postbuild

		#---------------------
		#1. step: find all wanted dependencies and create buildelements


		for target in conf["build"].get():
			order_target = BuildTarget(target)

			for source in conf["use"].get(target):
				#TODO: source may not be a source, but a ^/library.so.target
				#this happens when a target depends on another target
				order_file = SourceFile(source)

				crun = conf["c"].get(source)		#compiler
				crun += " " + conf["cflags"].get(source)	#compiler flags

				# encode the compiler flags etc
				objdir = conf["objdir"].get(source)

				#the encoded name: #TODO: maybe also encode the '/' in rsource
				encname = order_file.inname + "-" + generate_oname(crun)

				#assemble compiler output file without extension
				encpathname = relpath(objdir) + "/"
				encpathname += encname
				oname = encpathname + ".o"

				crun += " -c " + order_file.inname
				crun += " -o " + oname

				# add wanted (by config) dependency files (as smpath)
				file_depends = conf["depends"].get(source)
				#TODO: create object containers accordingly
				order_file.depends_wanted.union(file_depends)

				#add sourcefile path itself to depends
				ad = conf["autodepends"].get(source)

				if ad == "MD" or len(ad) == 0: # gcc MD enabled
					mdfile = encpathname + ".d"

					if os.path.isfile(mdfile):
						#if .d file exists, add its contents as wanted dependencies
						for dep in parse_dfile(mdfile):
							dependency_header = HeaderFile(dep)

							out_tmp = dependency_header.outname
							order_file.depends_wanted.add(out_tmp)
							self.filedict[out_tmp] = dependency_header
					else:
						#if MD is enabled but not yet present, we NEED to rebuild.
						order_file.needs_build = True

						#TODO: notification of first time .d generation?

					crun += " -MD"  # (re)generate c headers dependency file

				elif ad == "no":
					pass
				else:
					#let's not ignore an unknown autodetection mode bwahaha
					raise Exception(source + ": unknow autodetection mode: " + ad)

				order_file.loglevel = conf["loglevel"].get(source)
				order_file.crun = crun
				order_file.encname = encname
				order_file.outname = oname

				s_prb = conf["prebuild"].get(source)
				if len(s_prb) > 0:
					order_file.prebuild = s_prb

				s_pob = conf["postbuild"].get(source)
				if len(s_pob) > 0:
					order_file.postbuild = s_pob

				#TODO: pre/postbuild is not respected by that!
				#if encname already exists, we just overwrite it, good:
				self.filedict[oname] = order_file
				order_target.depends_wanted.add(oname)

			# <- for each target level
			order_target.loglevel = conf["loglevel"].get(target)
			ctrun = conf["c"].get(target)		#compiler for TARGET
			ctrun += " " + conf["cflags"].get(target)	#compiler flags
			ctrun += " " + conf["ldflags"].get(target)	#link flags
			ctrun += " -o " + relpath(target)		#target output name

			t_prb = conf["prebuild"].get(target)
			if len(s_prb) > 0:
				order_target.prebuild = t_prb

			t_pob = conf["postbuild"].get(target)
			if len(t_pob) > 0:
				order_target.postbuild = t_pob

			target_depends = conf["depends"].get(target)
			order_target.depends_wanted.union(target_depends)

			#append all object files for linkage
			#TODO: rewrite and relocate to somewhere else!
			for ofile in order_target.depends_wanted:
				ctrun += " " + relpath(ofile) #ofile.outname

			order_target.crun = ctrun

			#include current target to the build order
			self.filedict[order_target.outname] = order_target
			self.targets.add(order_target)

		#----------------------
		#2. step: reuse wanted dependencies to add buildelements to the correct hierarchy etc

		#TODO: this method does not respect all aspects of BuildElement.equals
		#e.g. it wil be a giant pile of crap with different pre/postbuilds

		for order_target in self.targets:

			for target_dependency in order_target.depends_wanted:
				#search the dependency and if exists, add it to 

				try:
					final_dependency = self.filedict[target_dependency]
				except KeyError:
					raise Exception("dependency " + target_dependency + " not found.")
				for sd in final_dependency.depends_wanted:
					sfinal_dep = self.filedict[sd]
					final_dependency.add_dependency(sfinal_dep)


				order_target.add_dependency(final_dependency)


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
		self.depends_wanted = set()	# wanted dependencies as smpaths
		self.depends_finished = set()
		self.name = smpath(name)
		self.inname = relpath(name)
		self.outname = ""
		self.encname = ""
		self.crun = ""
		self.prebuild = ""
		self.postbuild = ""
		self.needs_build = False	# does this file need to be rebuilt
		self.ready = False
		self.parents = set()	# the parent BuildElement may be notified of stuff
		self.worker = None
		self.loglevel = 2	# standard value?
		self.exitstate = 0
		self.finished = False
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
		notify parents that this dependency is ready
		'''

		self.finished = True

		domgr = not (manager == None)

		for parent in self.parents:
			parent.depends.remove(self)

			#TODO: suppress this via config
			parent.depends_finished.add(self)

			#print(repr(self) + " finished -> left parent.depends=" + repr(parent.depends))

			if domgr and parent.ready_to_build():
				manager.pending_jobs.remove(parent)
				manager.ready_jobs.add(parent)

	def add_parent(self, newp):
		self.parents.add(newp)

	def add_dependency(self, newone):
		'''adds a dependency to this compilation job'''
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
		newone.add_parent(self)
		self.depends.add(newone)


	def move_parent(self, old, new):
		'''renames (moves) a parent'''
		if not isinstance(old, BuildElement) or not isinstance(new, BuildElement):
			raise Exception("only BuildElements can be used to move parents")

		for dependency in self.depends:
			if old in dependency.parents:
				dependency.parents.remove(old)
				dependency.parents.add(new)

	def check_needs_build(self): #can/should be overridden if appropriate (e.g. header file)
		'''set self.needs_build to the correct value'''

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
		'''inname, outname, ready, encname, parents'''
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
		self.outname = relpath(tname) #TODO: respect suffix variables
		self.inname = "" #self.outname

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
	order.fill(variables)
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
