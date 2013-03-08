#!/usr/bin/python3

import threading
import multiprocessing
import os.path
import re
import base64
import concurrent.futures
import subprocess
import shlex
import time
import random


class vartest:
	def __init__(self, arg):
		self.l = arg
	def get(self, a = ""):
		return self.l

class vartestadv:
	def __init__(self):
		self.l = dict()

	def get(self, param):
		ret = self.l[param]
		print("getting [" + param + "]: " + str(ret))
		return ret

	def addv(self, key, val):
		self.l[key] = val


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
variables["build"] = vartest(["^/test", "^/liblol.so"])
variables["cflags"] = vartest("-O8 -flto=4")
variables["objdir"] = vartest("^/.objdir")

variables["use"] = vartestadv()
variables["depends"] = vartestadv()
variables["depends"].addv("^/gschicht.c", ['^/asdf.h'])
variables["depends"].addv("^/asdf.c", ['^/lol.h'])
variables["depends"].addv("^/lolfolder/file.c", ['^/asdf.h','^/lol.h'])
variables["depends"].addv("^/nahleut.c", [])
variables["use"].addv("^/test", ['^/asdf.c', '^/gschicht.c', '^/nahleut.c'])
variables["use"].addv("^/liblol.so", ['^/lolfolder/file.c'])

variables["autodepends"] = vartest("MD")
variables["prebuild"] = vartest("")
variables["postbuild"] = vartest("")
variables["loglevel"] = vartest("2")
variables["ldflags"] = vartest("-lsft")

print("var initialisation: \n" + str(variables) + "\n\n\n")



#TODO: when buildelements are used by multiple parents, detect that (e.g. header files) (respecting the differing variable values!)
#This means: extend the current tree model of dependencies to a graph model.

#TODO: colored output

#TODO: output queue, fixing thread interferences with msgs containing newlines

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
			if(self.job == None):
				#no more jobs available
				#so the worker can die!
				break

			print(repr(self) + ": fetched " + repr(self.job))
			self.job.worker = self

			if(self.job.check_needs_build()):
				#TODO: same output colors for each worker
				#print("[worker " + str(self.num) + "]:")
				print("" + repr(self) + ": making -> " + repr(self.job))
				self.job.run()
			else:
				print("" + repr(self) + ": skipped -> " + repr(self.job))

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
		if(not isinstance(order, BuildOrder)):
			raise Exception("Only a whole BuildOrder can be processed")

		for target in order.targets:
			self.submit(target)

		#TODO: respect verbosity and use repr/str/none/text()/whatevvur
		#print("\n\n Submitted: " + order.text())



	def submit(self, job):
		"""insert a job and it's dependencies in the execution queue"""
		if(not isinstance(job, BuildElement)):
			raise Exception("only BuildElements can be submitted")

		job.add_deps_to_manager(self)

	def submit_single(self, job):
		"""insert a single job in the correct job queue"""
		if(not isinstance(job, BuildElement)):
			raise Exception("only BuildElements can be submitted")

		with self.job_lock:
			if(job.ready_to_build()):
				self.ready_jobs.add(job)
			else:
				self.pending_jobs.add(job)

	def finished(self, job):
		'''must be called when a job is done executing'''
		with self.job_lock:
			if(job.exitstate == 0):
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
			if(len(self.ready_jobs) > 0):

				if(self.error != 0):
					return None

				newjob = self.ready_jobs.pop()
				self.running_jobs.add(newjob)
				return newjob

			#TODO: could cause errors, investigate pls
			elif(len(self.running_jobs) > 0 and len(self.pending_jobs) > 0):
				#if no jobs are ready, then remaining(pending) jobs are unlocked by currently running jobs
				#so the current worker has to wait here, until a job is ready, errors occur, or all jobs died.

				self._find_ready_jobs()
				self.job_lock.wait_for(self.nextjob_continue)

				if(self.error != 0 or len(self.ready_jobs) == 0):
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

		if(len(self.failed_jobs) > 0):
			print("==========\nFAILED jobs:")
			for job in self.failed_jobs:
				print(repr(job))

		if(len(self.ready_jobs) > 0):
			print("++++++++++\njobs currently ready to build:")
			for job in self.ready_jobs:
				print(repr(job))

		if(len(self.pending_jobs) > 0):
			#not all jobs have been built
			print("++++++++++\njobs blocked by dependencies:")
			for job in self.pending_jobs:
				print(repr(job))

		if(len(self.finished_jobs) > 0):
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
		if(re.match(".*\\.(h|hpp)", filename)):
			#print(filename + " generated HeaderFile")
			return self.find_create_header(filename)
		else:
			return SourceFile(filename)

	def find_create_header(self, fname):
		'''if not yet existing, this HeaderFile is created and returned'''
		rname = relpath(fname)

		print("self.filedict: " + str(self.filedict))

		if(rname in self.filedict):
			print("reusing " + fname)
			return self.filedict[rname]
		else:
			newheader = HeaderFile(fname)
			self.filedict[rname] = newheader
			return newheader


	def fill(self, conf):
		'''
		fill this BuildOrder with contents for later processing

		attention: black magic is involved here.
		'''

		for target in conf["build"].get():
			order_target = BuildTarget(target)

			for source in conf["use"].get(target):
				#TODO: reuse source files if it's identical
				order_file = SourceFile(source)

				crun = conf["c"].get(source)		#compiler
				crun += " " + conf["cflags"].get(source)	#compiler flags
				crun += " -c " + relpath(source)		#sourcefile name

				# encode the compiler flags etc
				objdir = conf["objdir"].get(source)

				#the encoded name 
				
				encname = generate_oname(crun)
				order_file.encname = encname
				encpathname = relpath(objdir) + "/" + relpath(source) + "-" + encname

				o_name = encpathname + ".o"
				order_file.set_outname(o_name)
				crun += " -o " + o_name			#output object file name generation

				# add known (by config) dependency files
				file_depends = conf["depends"].get(source)
				print("processing " + source + ": \n -----")
				for dep in file_depends:
					#TODO: a compilation/whatever can be dependent on e.g. a library.
					d = self.build_element_factory(dep)
					order_file.add_dependency(d)
				
				#add sourcefile path itself to depends
				ad = conf["autodepends"].get(source)

				if(ad == "MD"):
					mdfile = encpathname + ".d"

					if(os.path.isfile(mdfile)):
						#if .d file exists, parse its contents as dependencies
						for dep in parse_dfile(mdfile):
							order_file.add_dependency(self.find_create_header(dep))
					else:
						#TODO: notification of first time .d generation?
						pass

					crun += " -MD"  # (re)generate c headers dependency file

				elif(ad == "no"):
					#TODO: maybe a warning of the MD skipping
					pass
				else:
					#let's not ignore an unknown autodetection mode bwahaha
					raise Exception(source + ": unknow autodetection mode: " + ad)

				order_file.loglevel = conf["loglevel"].get(source)

				s_prb = conf["prebuild"].get(source)
				if(len(s_prb) > 0):
					order_file.prebuild = s_prb

				s_pob = conf["postbuild"].get(source)
				if(len(s_pob) > 0):
					order_file.postbuild = s_pub

				# compiler invocation complete -> add it to the source file build order
				order_file.set_crun(crun)

				order_target.add_dependency(order_file)

			#=> continuation for each target

			ctrun = conf["c"].get(target)		#compiler for TARGET
			ctrun += " " + conf["cflags"].get(target)	#compiler flags
			ctrun += " " + conf["ldflags"].get(target)	#link flags
			ctrun += " -o " + relpath(target)		#target output name

			#append all object files for linkage
			for ofile in order_target.depends:
				ctrun += " " + ofile.outname

			#TODO: a compilation/whatever can be dependent on e.g. a library.

			t_prb = conf["prebuild"].get(target)
			if(len(s_prb) > 0):
				order_target.prebuild = t_prb

			s_pob = conf["postbuild"].get(target)
			if(len(s_pob) > 0):
				order_target.postbuild = t_pob

			order_target.set_crun(ctrun)

			#include current target to the build order
			self.targets.add(order_target)

		#direct function level here

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
		self.loglevel = 2 #TODO: get from variables
		self.exitstate = 0
		self.finished = False

	def run(self):
		raise NotImplementedError("Implement this shit for a working compilation...")

	def add_deps_to_manager(self, manager):
		#TODO: respect graph model instead of tree
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

			print(repr(self) + " finished -> left parent.depends=" + repr(parent.depends))

			if(domgr and parent.ready_to_build()):
				manager.pending_jobs.remove(parent)
				manager.ready_jobs.add(parent)


	def add_parent(self, newp):
		self.parents.add(newp)

	def add_dependency(self, newone):
		'''adds a dependency to this compilation job'''
		if(type(newone) == list):
			for e in newone:
				if(not isinstance(newone, BuildElement)):
					raise Exception("only BuildElements can be added as a dependency for another BuildElement")

				print(repr(self) + " -> adding dependency from list " + repr(newone))
				e.add_parent(self)
				self.depends.add(e)

		else:
			if(not isinstance(newone, BuildElement)):
				raise Exception("only BuildElements can be added as a dependency for another BuildElement")

			print(repr(self) + " -> adding dependency " + repr(newone))
			newone.add_parent(self)
			self.depends.add(newone)

	def check_needs_build(self): #can/should be overridden if appropriate (e.g. header file)
		'''set self.needs_build to the correct value'''

		if(os.path.isfile(self.outname)):
			if (os.path.getmtime(self.outname) < os.path.getmtime(self.inname)):
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
				if(os.path.getmtime(fl) > os.path.getmtime(self.outname)):
					self.needs_build = True
					print("==> Build needed: " + repr(d) + " is newer than " + self.outname)
					break

			except OSError as e:
				print(str(e) + " -> Ignoring for now.")

		self.finished = not self.needs_build
		return self.needs_build

	def ready_to_build(self):
		'''when all dependencies are done, return true'''
		if(len(self.depends) > 0):
			self.ready = False
		else:
			self.ready = True
		return self.ready

	def set_crun(self, crun):
		self.crun = crun

	def text(self, depth=0):
		'''inname, outname, ready, encname, parents'''
		space = ''.join(['\t' for i in range(depth)])
		out = space + "++++ " + str(type(self)) + " " + str(id(self)) + "\n"


		if(self.inname):
			out += space + "* Input filename: " + self.inname + "\n"

		if(self.outname):
			out += space + "* Output filename: " + self.outname + "\n"

		deps_done = len(self.depends_finished)
		deps_pending = len(self.depends)
		deps_sum = deps_done + deps_pending

		out += space + "--- status: " + str(self.exitstate) + " ---\n"

		if(deps_sum > 0):
			deps_percent =  "{0:.2f}".format(float(deps_done/deps_sum) * 100)


			out += space + "--- deps: ["
			out += str(deps_done) + "/" + str(deps_sum) + "] "
			out += "[" + deps_percent + "%"
			out += "] ---\n"


			if(len(self.depends) > 0):
				out += space + "--- pending dependencies:\n"
				for f in self.depends:
					out += f.text(depth + 1)
					out += space + "---\n"

			if(len(self.depends_finished) > 0):
				out += space + "--- finished dependencies:\n"

				for f in self.depends_finished:
					out += f.text(depth + 1)
					out += space + "---\n"
		else:
			out += space + "* NO dependencies\n"

		if(self.ready):
			if(self.finished):
				out += space + "* BUILT SUCCESSFULLY\n"
			else:
				if(self.exitstate != 0):
					out += space + "* FAILED\n"
				else:
					out += space + "* READY TO BUILD\n"
		else:
			if(len(self.depends) > 0):
				out += space + "* BLOCKED BY DEPENDENCIES\n"
			else:
				out += space + "* NOT READY\n"

		out += space + "++++\n"

		return out


class HeaderFile(BuildElement):
	"""headerfile for a source file, never needs to be built"""

	def __init__(self, hname):
		BuildElement.__init__(self, hname)
		#no need to set self.outname, as we never need it

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

		if(self.prebuild):
			print("prebuild for " + self + " '" + self.prebuild + "'")
			#TODO: os.system()
			#ret = subprocess.call(shlex.split(self.prebuild), shell=False)

		if(ret != 0):
			failat = "prebuild for"
		else:
			print(repr(self.worker) + " == building -> " + repr(self))

			## compiler is launched here
			#TODO: correct invocation
			print(repr(self.worker) + ": EXEC:: " + self.crun)
			#ret = subprocess.call(shlex.split(self.crun), shell=False)
			time.sleep(1)

			print(repr(self.worker) + " == done building -> " + repr(self))

		#TODO: don't forget to remove...
		ret = random.choice([0,0,0,0,1,8])

		if(ret != 0):
			failat = "compiling"
		else:
			if(self.postbuild):
				print("postbuild for " + repr(self) + " '" + self.postbuild + "'")
				#ret = subprocess.call(shlex.split(self.postbuild), shell=False)
			if(ret != 0):
				failat = "postbuild for"

		if(ret > 0):
			print("\n======= Fail at " + failat +" " + repr(self) + " =========")
			print("Error when building " + repr(self) )
			self.exitstate = ret
		else:
			self.exitstate = 0

	def set_outname(self, newo):
		self.outname = newo

	def __repr__(self):
		return self.inname

	def __str__(self):
		out = "\n===========\nsource file: " + repr(self) + " -> \n"
		n = 0
		for d in self.depends:
			out += "\tdep " + str(n) + ":\t" + repr(d) + "\n"
			n += 1

		out += "\tc-invokation: " + self.crun + "\n===========\n"
		return out


class BuildTarget(BuildElement):
	'''A build target has a list of all files that will be linked in the target'''

	def __init__(self, tname):
		BuildElement.__init__(self, tname)
		self.name = tname
		self.outname = relpath(tname) #TODO: respect suffix variables
		self.inname = "" #self.outname

	def set_crun(self, crun):
		self.crun = crun

	def run(self):
		'''this method compiles a single target.'''

		ret = 0		#return value storage

		if(self.prebuild):
			print("prebuild for " + repr(self) + " '" + self.prebuild + "'")
			#ret = subprocess.call(shlex.split(self.prebuild), shell=False)

		if(ret != 0):
			failat = "prebuild for"
		else:
			print("== linking -> " + repr(self))

			## compiler is launched here
			#TODO: correct invocation
			print(repr(self.worker) + ": " + repr(self))
			#ret = subprocess.call(shlex.split(self.crun), shell=False)
			time.sleep(1)

			print("== done linking -> " + repr(self))

		#TODO: don't forget to remove...
		ret = random.choice([0,0,1])

		if(ret != 0):
			failat = "linking"
		else:
			if(self.postbuild):
				print("postbuild for " + repr(self) + " '" + self.postbuild + "'")
				#ret = subprocess.call(shlex.split(self.postbuild), shell=False)

			if(ret != 0):
				failat = "postbuild for"

		if(ret > 0):
			fail = True
		else:
			fail = False

		if fail:
			print("\n======= Fail at " + failat +" " + repr(self) + " =========")
			print("Error when linking " + repr(self) )
			self.exitstate = ret
		else:
			self.exitstate = 0

	def __str__(self):
		out = "\n>>>>>>>>>>>>>>>>>>>>>>>>>\ntarget file: " + relpath(self.name)
		out += " -> \n"
		n = 0
		for f in self.depends:
			out += "\n-- file " + str(n) + ":" + str(f)
			n += 1
		out += "\t c-invokation: " + self.crun + "\n>>>>>>>>>>>>>>>>>>>>>>>>>\n"
		return out

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

	m = JobManager()
	m.queue_order(order)

	print(order.text())

	m.start()
	m.join()

	#show status after the build
	print(order.text())

	#after all targets:
	if(m.get_error() == 0):
		print("sftmake builder shutting down regularly")
	else:
		print("sftmake builder exiting due to error")


if __name__ == "__main__":
	main()
