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


class BuildJob:
	"""one build job, will build a BuildThing"""

	def __init__(self, job):
		self.manager = None    #manager calls set_manager upon submission

		if(not isinstance(job, BuildThing)):
			raise Exception("only a BuildThing can be a processed with a BuildJob")
		else:
			self.job = job

	def set_manager(self, manager):
		"""set the BuildManager if this BuildJob"""
		self.manager = manager


class BuildWorker:
	"""A worker thread that works and behaves like a slave. Be careful, it bites."""

	def __init__(self, manager):
		self.thread = threading.Thread(target=self.run)
		self.current_job = None

	def run(self):
		pass


class JobStatus:
	"""status wrapper for a BuildJob"""

	def __init__(self, job):
		self.running = False
		self.exitstate = 0
		if(not isinstance(job, BuildJob)):
			raise Exception("Only a BuildJob can be wrapped by JobStatus")
		else:
			self.job = job

	def status(self):
		self.job.thread.join()
		return self.exitstate


class JobManager:
	"""thread manager for invoking the compilers"""

	def __init__(self, max_workers=get_thread_count()):
		self.workers = []
		self.waiting_jobs = set()
		self.ready_jobs = set()
		self.finished_jobs = set()
		self.max_workers = max_workers

	def submit(self, job):
		"""insert a function in the execution queue"""
		if(not isinstance(job, BuildJob)):
			raise Exception("only BuildJobs can be submitted")

		job.set_manager(self)
		newone = JobStatus(job) #the new job gets it's own status wrapper
		self.pending_jobs.append(newone)

	def finished(self, jobstatus):
		if(jobstatus.success()):
			job = jobstatus.get_job()
			self.finished_jobs.add(job)
		else
			#TODO: somehow kill everybody/thing
			pass

	def get_next(self):
		if(len(self.ready_jobs) > 0):
			newjob = self.ready_jobs.pop()
			return newjob
		else:
			return None

	def _create_workers(self):
		'''creates all BuildWorkers'''
		for(i in range(self.max_workers)):
			newworker = BuildWorker(self)
			self.workers.append(newworker)

	def _launch_workers(self):
		#TODO: make workers aware of the pending jobs
		pass

	def run(self):
		"""launch the maximum number of concurrent jobs"""
		self._create_workers()
		self._launch_workers()


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

class BuildThing:

	def __init__(self, name):
		self.depends = set()
		self.name = smpath(name)
		self.inname = relpath(name)
		self.outname = ""
		self.encname = ""
		self.c_run = ""
		self.prebuild = ""
		self.postbuild = ""
		self.needs_build = False	# does this file need to be rebuilt
		self.parent = None			# the parent BuildThing may be notified of stuff #TODO: actually use
		self.loglevel = 2 #TODO: sure?

	def run(self):
		raise NotImplementedError("Implement this shit for a working compilation...")

	def add_dependency(self, newone):
		'''adds a dependency to this compilation job'''

		if(not isinstance(newone, BuildThing)):
			raise Exception("only BuildThings can be added as a dependency for another BuildThing")

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
			for fl in self.depends:
				try:
					# check for modification times
					print("checking mtime of -> " + fl)
					if(os.path.getmtime(fl) > os.path.getmtime(self.outname)):
						self.needs_build = True
						print("==> Build needed: " + fl + " is newer than " + self.outname)
						break

				except OSError as e:
					print(str(e) + " -> Ignoring for now.")

	def check_ready_to_build(self):
		pass

	def set_c_run(self, c_run):
		self.c_run = c_run


class HeaderFile(BuildThing):
	"""headerfile for a source file, never needs to be built"""

	def __init__(self, hname):
		BuildThing.__init__(self, hname)

	def check_needs_build(self):
		self.needs_build = False

	def run(self):
		#hahahahaha
		pass

class SourceFile(BuildThing):
	"""a source file that is compiled to an object file"""

	def __init__(self, filename):
		BuildThing.__init__(self, filename)

	def set_encname(self, new_enc):
		self.encname = new_enc
		self.outname = self.encname + ".o"

	def run(self):
		'''this method compiles a the file into a single object.'''

		if(self.needs_build):

			ret = 0

			if(self.prebuild):
				print("prebuild for " + self + " '" + self.prebuild + "'")
				#ret = subprocess.call(shlex.split(self.prebuild), shell=False)
				pass

			if(ret != 0):
				failat = "prebuild for"
				pass
			else:
				print("== building -> " + c_name)

				## compiler is launched here
				#TODO: correct invocation
				#ret = subprocess.call(shlex.split(self.c_run), shell=False)
				time.sleep(1)

				print("== done building -> " + c_name)

			#TODO: don't forget to remove...
			if(manager.error == 0): #generate ONE random build fail
				ret = round(random.random())
			else:
				ret = 0

			if(ret != 0):
				failat = "compiling"
			else:
				if(self.postbuild):
					print("postbuild for " + self + " '" + self.postbuild + "'")
					#ret = subprocess.call(shlex.split(self.postbuild), shell=False)
					pass
				if(ret != 0):
					failat = "postbuild for"

			if(ret > 0):
				fail = True
			else:
				fail = False

			if fail:
				print("\n======= Fail at "+ failat +" " + repr(self) + " =========")
				manager.error = ret
				print("Error when building "+ c_name )
				return ret
			else:
				return 0

		#doesn't need build
		else:
			print("skipping " + c_name)

	def add_dependency(self, dfile):
		if(type(dfile) == list):
			self.depends += dfile
		else:
			self.depends.append(dfile)

	def __repr__(self):
		return relpath(self.name)

	def __str__(self):
		out = "\n===========\nsource file: " + relpath(self.name) + " -> \n"
		n = 0
		for d in self.depends:
			out += "\tdep " + str(n) + ":\t" + relpath(d) + "\n"
			n += 1

		out += "\tc_invokation: " + self.c_run + "\n===========\n"
		return out


class BuildTarget(BuildThing):
	'''A build target has a list of all files that will be linked in the target'''

	def __init__(self, tname):
		self.files = []
		self.name = tname

	def add_file(self, cfile):
		if(not isinstance(cfile, BuildFile)):
			raise Exception("a target can only have BuildFiles as dependency")
		else:
			cfile.set_target(self)
			self.files.append(cfile)

	def set_c_run(self, c_run):
		self.c_run = c_run

	def check_needs_build(self):
		if(not os.path.isfile(t_name)):
			self.needs_build = True
		#TODO: check the dependencies etc

	def run(self):
		'''this method compiles a single target.'''

		if(self.needs_build):

			ret = 0

			if(self.prebuild):
				print("prebuild for " + self.name + " '" + self.prebuild + "'")
				#ret = subprocess.call(shlex.split(self.prebuild), shell=False)
				pass

			if(ret != 0):
				failat = "prebuild for"
			else:
				print("== linking -> " + self.name)

				## compiler is launched here
				#TODO: correct invocation
				#ret = subprocess.call(shlex.split(self.c_run), shell=False)
				time.sleep(1)

				print("== done linking -> " + self.name)

			#TODO: don't forget to remove...
			ret = round(random.random())

			if(ret != 0):
				failat = "linking"
			else:
				if(self.postbuild):
					print("postbuild for " + self.name + " '" + self.postbuild + "'")
					#ret = subprocess.call(shlex.split(self.postbuild), shell=False)
					
				if(ret != 0):
					failat = "postbuild for"

			if(ret > 0):
				fail = True
			else:
				fail = False

			if fail:
				print("\n======= Fail at "+ failat +" " + t_name + " =========")
				manager.error = ret
				print("Error when linking "+ t_name )
				return ret
			else:
				return 0

		#doesn't need build
		else:
			print("skipping " + c_name)

	def __str__(self):
		out = "\n>>>>>>>>>>>>>>>>>>>>>>>>>\ntarget file: " + relpath(self.name)
		out += " -> \n"
		n = 0
		for f in self.depends:
			out += "\n-- file " + str(n) + ":" + str(f)
			n += 1
		out += "\t c_invokation: " + self.c_run + "\n>>>>>>>>>>>>>>>>>>>>>>>>>\n"
		return out





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
					self.m.submit(BuildJob(ofile))

			self.m.submit(BuildJob(target))

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

				c_run = self.conf["c"].get(source)		#compiler
				c_run += " " + self.conf["cflags"].get(source)	#compiler flags
				c_run += " -c " + relpath(source)		#sourcefile name

				# encode the compiler flags etc
				objdir = self.conf["objdir"].get(source)
				enc_name = relpath(objdir) + "/" + relpath(source) + "-" + generate_oname(c_run)	#TODO: This line contains 99% bugs
				order_file.set_encname(enc_name)

				o_name = enc_name + ".o"
				c_run += " -o " + o_name	 		#output object file name generation

				# add known (by config) dependency files
				order_file.add_dependency(self.conf["depends"].get(source))
				
				#add sourcefile path itself to depends
				ad = self.conf["autodepends"].get(source)

				if(ad == "MD"):
					mdfile = enc_name + ".d"

					if(os.path.isfile(mdfile)):
						#if .d file exists, parse its contents as dependencies
						order_file.add_dependency(parse_dfile(mdfile))
					else:
						#TODO: notification of first time .d generation
						pass

					c_run += " -MD"  # (re)generate c headers dependency file

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
				order_file.set_c_run(c_run)


				order_target.add_file(order_file)
				#print(str(order_file))

			#=> continuation for each target

			ct_run = self.conf["c"].get(target)		#compiler for TARGET
			ct_run += " " + self.conf["cflags"].get(target)	#compiler flags
			ct_run += " " + self.conf["ldflags"].get(target)	#link flags
			ct_run += " -o " + relpath(target)		#target output name

			#append all object files for linkage
			#TODO: shouldn't this be generated in the target job?
			for ofile in order_target.files:
				ct_run += " " + relpath(ofile.enc_name + ".o")

			t_prb = self.conf["prebuild"].get(target)
			if(len(s_prb) > 0):
				order_target.prebuild = t_prb

			s_pob = self.conf["postbuild"].get(target)
			if(len(s_pob) > 0):
				order_target.postbuild = t_pob

			order_target.set_c_run(ct_run)

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
