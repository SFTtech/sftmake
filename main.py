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


class vartest():
	def __init__(self, arg):
		self.l = arg
	def get(self, a = ""):
		return self.l


try:
	smpath("/tmp/a")
except NameError:
	print("redefining smpath() as stub")
	def smpath(path):
		'''stub for testing'''
		return path

try:
	relpath("^/a")
except NameError:
	print("redefining relpath() as stub")
	def relpath(path):
		'''stub for testing'''
		return path

try:
	generate_oname("gschicht")
except NameError:
	print("redefining generate_oname() as stub")
	def generate_oname(name):
		encoded = base64.b64encode(bytearray(name, 'utf-8'))
		return encoded.decode('utf-8')


#test purpose only
variables = {}
variables["c"] = vartest("gcc")
variables["build"] = vartest(["^/test", "^/liblol.so"])
variables["cflags"] = vartest("-O8 -flto=4")
variables["use"] = vartest(["^/gschicht.c", "^/asdf.c", "^/lolfolder/file.c"])
variables["objdir"] = vartest("^/.objdir")
variables["depends"] = vartest(['^/asdf.h','^/lol.h'])
variables["autodepends"] = vartest("MD")
variables["prebuild"] = vartest("")
variables["postbuild"] = vartest("")
variables["loglevel"] = vartest("2")
variables["ldflags"] = vartest("-lsft")


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

	def __init__(self, manager, num):
		self.thread = threading.Thread(target=self.run)
		self.manager = manager
		self.num = num
		self.job = None		#The BuildElement currently being processed by this worker

	def run(self):
		while True:
			self.job = self.manager.get_next()
			if(self.job == None):
				#no more jobs available
				#so the worker can die!
				return

			self.job.set_worker(self)

			if(self.job.needs_build):
				#TODO: same output colors for each worker
				#print("[worker " + str(self.num) + "]:")
				self.job.run()

			self.manager.finished(self.job)

	def start(self):
		self.thread.start()


class JobManager:
	"""thread manager for invoking the compilers"""

	def __init__(self, max_workers=get_thread_count()):
		self.workers = []

		self.pending_jobs = set()		# jobs that will be processed sometime
		self.ready_jobs = set()		# jobs that are ready to be executed
		self.running_jobs = set()		# currently executing jobs
		self.finished_jobs = set()		# jobs that were executed successfully
		self.max_workers = max_workers	# worker limitation

		self.error = 0
		self.erroreus_job = None

		self.job_lock = threading.Condition()

	def submit(self, job):
		"""insert a function in the execution queue"""
		if(not isinstance(job, BuildContainer)):
			raise Exception("only BuildContainers can be submitted")

		with self.job_lock:
			job.set_manager(self)
			self.pending_jobs.add(job)

	def finished(self, job):
		with self.job_lock:
			if(job.success()):
				self.running_jobs.remove(job)
				self.finished_jobs.add(job)
				job.notify_parents()
				self._find_ready_jobs()
				self.job_lock.notify()
				#TODO: notify the get_next block (down there vvv)
			else
				self.error = job.exitstate
				self.erroreus_job = job

	def get_next(self):
		with self.job_lock:
			if(len(self.ready_jobs) > 0):
				newjob = self.ready_jobs.pop()
				self.running_jobs.add(newjob)
				return newjob

			else if(len(self.running_jobs) > 0 && len(self.pending_jobs) > 0):
				#running jobs are probably blocking the pending_jobs
				self.job_lock.wait_for(len(self.ready_jobs) > 0 && self.error == 0)
				newjob = self.ready_jobs.pop()
				self.running_jobs.add(newjob)
				return newjob

			else: #we are out of jobs!
				return None

	def _find_ready_jobs(self):
		with self.job_lock:
			new_ready_jobs = filter(lambda job: job.ready_to_build, self.pending_jobs)
			self.pending_jobs -= new_ready_jobs
			self.ready_jobs |= new_ready_jobs

			#old version:
#			for(job in self.pending_jobs):
#				if(job.ready_to_build()):
#					self.pending_jobs.remove(job)
#					self.ready_jobs.add(job)

	def _create_workers(self):
		'''creates all BuildWorkers'''
		for(i in range(self.max_workers)):
			newworker = BuildWorker(self)
			self.workers.append(newworker)

	def _launch_workers(self):
		"""all worker threads are launched"""
		for(worker in self.workers):
			worker.start()

	def run(self):
		"""launch the maximum number of concurrent jobs"""
		self._create_workers()
		self._find_ready_jobs()
		self._launch_workers()

	def join(self):
		"""wait here for all jobs to finish"""
		#TODO
		if(len(self.pending_jobs) > 0):
			#not all jobs have been built
			print("\nnot all jobs have been built:")
			for(job in self.pending_jobs):
				print(repr(job))


class BuildOrder:
	'''A build order contains all targets that must be built'''

	def __init__(self):
		self.targets = []
		self.max_jobs = get_thread_count()
	def add_target(self, target):
		self.targets.append(target)
	def job_count(self, n = get_thread_count()):
		self.max_jobs = n

	def __str__(self):
		out = "\n\n%%%%%%%%%%%%%%%%%\n BUILD ORDER"
		for t in self.targets:
			out += str(t)
		out += "\n%%%%%%%%%%%%%%%%%\n"
		return out


class BuildElement:

	def __init__(self, name):
		self.depends = set()
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
		self.loglevel = 2 #TODO: sure?
		self.exitstate = 0

	def run(self):
		raise NotImplementedError("Implement this shit for a working compilation...")

	def notify_parents():
		'''upon a successful run, notify parents that this dependency is ready'''
		for(parent in self.parents):
			parent.depends.remove(self)
		pass


	def set_worker(self, worker):
		'''set the worker of this BuildElement'''
		self.worker = worker

	def success(self):
		#TODO: eventually wait til termination of job
		#TODO: or: just return a status that maybe says "not ready yet"
		return (self.exitstate == 0)

	def add_dependency(self, newone):
		'''adds a dependency to this compilation job'''

		if(not isinstance(newone, BuildElement)):
			raise Exception("only BuildElements can be added as a dependency for another BuildElement")

		self.depends.add(newone)

	def check_needs_build(self): #can/should be overridden if appropriate (e.g. header file)
		'''set self.needs_build to the correct value'''

		if(os.path.isfile(self.outname)):
			if (os.path.getmtime(self.outname) < os.path.gettime(self.inname)):
				self.needs_build = True
			else:
				self.needs_build = False

		else: # outname does not exist
			self.needs_build = True

		#only check dependencies, if thing itself doesn't need a build
		if(not self.needs_build):
			for d in self.depends:
				try:
					# check for modification times
					print("checking mtime of -> " + repr(d))
					if(os.path.getmtime(fl) > os.path.getmtime(self.outname)):
						self.needs_build = True
						print("==> Build needed: " + repr(d) + " is newer than " + self.outname)
						break

				except OSError as e:
					print(str(e) + " -> Ignoring for now.")

	def ready_to_build(self):
	'''when all dependencies are ready (or no more dependencies), return true'''
		self.ready = True
		for(d in self.depends):
			if(not d.ready_to_build()):
				self.ready = False
				break
		return self.ready

	def set_crun(self, crun):
		self.crun = crun


class HeaderFile(BuildElement):
	"""headerfile for a source file, never needs to be built"""

	def __init__(self, hname):
		BuildElement.__init__(self, hname)
		#no need to set self.outname, as we never need it

	def check_needs_build(self):
		self.needs_build = False

	def run(self):
		print("[" + self.worker.num + "]: " + repr(self))

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
			#ret = subprocess.call(shlex.split(self.prebuild), shell=False)

		if(ret != 0):
			failat = "prebuild for"
		else:
			print("== building -> " + repr(self))

			## compiler is launched here
			#TODO: correct invocation
			print("[" + self.worker.num + "]: " + repr(self))
			#ret = subprocess.call(shlex.split(self.crun), shell=False)
			time.sleep(1)

			print("== done building -> " + repr(self))

		#TODO: don't forget to remove...
		ret = round(random.random())

		if(ret != 0):
			failat = "compiling"
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
			print("Error when building " + repr(self) )
			self.exitstate = ret
		else:
			self.exitstate = 0
		return self.exitstate

	def add_dependency(self, dfile):
		if(type(dfile) == list):
			self.depends += dfile
		else:
			self.depends.append(dfile)

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
		self.files = []
		self.name = tname
		self.outname = relpath(tname)
		self.inname = self.outname

	def add_file(self, cfile):
		if(not isinstance(cfile, BuildFile)):
			raise Exception("a target can only have BuildFiles as dependency")
		else:
			cfile.set_target(self)
			self.files.append(cfile)

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
			print("[" + self.worker.num + "]: " + repr(self))
			#ret = subprocess.call(shlex.split(self.crun), shell=False)
			time.sleep(1)

			print("== done linking -> " + repr(self))

		#TODO: don't forget to remove...
		ret = round(random.random())

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
		return self.exitstate

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



class Builder:
	"""Class for using and preparing the sftmake build process"""
	def __init__(self, conf):
		self.conf = conf

	def build(self, order):
		'''process a BuildOrder -> compile everything needed'''

		if(type(order) != BuildOrder):
			raise Exception("Builder: the build() function needs a BuildOrder")

		#TODO: job limiting
		self.m = JobManager(max_workers=get_thread_count())

		targetsstr = "'"
		for t in order.targets:
			targetsstr += t.name + " "
		targetsstr += "'"
		print("\n\norder contains " + targetsstr)

		for target in order.targets:
			rtarget = relpath(target.name)

			#submit all new jobs to queue:
			for ofile in target.files:
				self.m.submit(ofile)

			self.m.submit(target)

		self.m.start()
		self.m.join()

		#after all targets:
		if(self.m.get_error() == 0):
			print("sftmake shutting down...")
		else:
			print("errors caused sftmake to exit")


	def prepare(self):
		'''generate a BuildOrder for later processing'''
		order = BuildOrder()
		for target in self.conf["build"].get():
			order_target = BuildTarget(target)

			for source in self.conf["use"].get(target):
				order_file = SourceFile(source)

				crun = self.conf["c"].get(source)		#compiler
				crun += " " + self.conf["cflags"].get(source)	#compiler flags
				crun += " -c " + relpath(source)		#sourcefile name

				# encode the compiler flags etc
				objdir = self.conf["objdir"].get(source)

				#the encoded name 
				
				encname = generate_oname(crun)
				order_file.encname = encname
				encpathname = relpath(objdir) + "/" + relpath(source) + "-" + encname

				o_name = encpathname + ".o"
				order_file.outname = o_name
				crun += " -o " + o_name			#output object file name generation

				# add known (by config) dependency files
				order_file.add_dependency(self.conf["depends"].get(source))
				
				#add sourcefile path itself to depends
				ad = self.conf["autodepends"].get(source)

				if(ad == "MD"):
					mdfile = encpathname + ".d"

					if(os.path.isfile(mdfile)):
						#if .d file exists, parse its contents as dependencies
						order_file.add_dependency(parse_dfile(mdfile))
					else:
						#TODO: notification of first time .d generation
						pass

					crun += " -MD"  # (re)generate c headers dependency file

				elif(ad == "no"):
					#kp evtl auch iwas
					pass
				else:
					#let's not ignore an unknown autodetection mode bwahaha
					raise Exception(source + ": unknow autodetection mode: " + ad)

				order_file.loglevel = self.conf["loglevel"].get(source)

				s_prb = self.conf["prebuild"].get(source)
				if(len(s_prb) > 0):
					order_file.prebuild = s_prb

				s_pob = self.conf["postbuild"].get(source)
				if(len(s_pob) > 0):
					order_file.postbuild = s_pub

				# compiler invocation complete -> add it to the source file build order
				order_file.set_crun(crun)


				order_target.add_file(order_file)
				#print(str(order_file))

			#=> continuation for each target

			ctrun = self.conf["c"].get(target)		#compiler for TARGET
			ctrun += " " + self.conf["cflags"].get(target)	#compiler flags
			ctrun += " " + self.conf["ldflags"].get(target)	#link flags
			ctrun += " -o " + relpath(target)		#target output name

			#append all object files for linkage
			#TODO: shouldn't this be generated in the target job?
			for ofile in order_target.files:
				ctrun += " " + ofile.outname

			t_prb = self.conf["prebuild"].get(target)
			if(len(s_prb) > 0):
				order_target.prebuild = t_prb

			s_pob = self.conf["postbuild"].get(target)
			if(len(s_pob) > 0):
				order_target.postbuild = t_pob

			order_target.set_crun(ctrun)

			#include current target to the build order
			order.add_target(order_target)

		#direct function level
		print(str(order))
		return order



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
	hmatch = re.compile(r"[-\w/\.]+\.(h|hpp)") #matches a single header file
	parts = re.split(r"\s+", line)

	#return all matching header files as list
	return filter(lambda part: hmatch.match(part), parts)
#	return [ part for part in parts if hmatch.match(part) ]




def main():
	print("fak u dolan")
	#print(str(variables["build"].get()))
	builder = Builder(variables)
	order = builder.prepare()
	builder.build(order)


if __name__ == "__main__":
	main()
