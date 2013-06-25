#!/usr/bin/python3

# this file is, you guessed it, part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
#
# test routine for the sftmake builder
#
# (c) 2013 [sft]technologies, jonas jelten


#TODO: unit-test-class


import builder
import pprint
import conf

#test classes which simulate conf.py behavior

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


def initvars0():
	#variable configuration for the testproject

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

	return variables, confinfo


def initvars1():
	'''
	approach of creating the config via python by using conf.py
	'''

	variables = dict()

	conf_project = conf.Config(name="project", conftype=conf.Config.TYPE_BASE, parents = [conf.conf_default], directory='^')

	#TODO: this has to be generated by the dirscanner!
#	conf_root = conf.Config('^', conf.Config.TYPE_DIR, [conf_project], '^')
#	conf_main = conf.Config('^/main.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_lib0 = conf.Config('^/library0.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_lib1 = conf.Config('^/library1.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_both = conf.Config('^/both.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_lib = conf.Config('^/liblol.so', conf.Config.TYPE_TARGET, [conf_root], '^')
#	conf_bin = conf.Config('^/lolbinary', conf.Config.TYPE_TARGET, [conf_root], '^')


	import dirscanner, util

	projectpath = "./sftmake-testproject"

	filetree = dirscanner.smtree(rootpath=projectpath)
	util.set_smroot(filetree.get_root_smfile().directory)

	smfile_handlers = []
	for f in filetree.smfiles:
		new_handler = f.create_handler()
		new_handler.run()
		smfile_handlers.append(new_handler)
		print(str(new_handler))

	cconf = conf.Var(name='c', valtype=conf.Var.TYPE_STRING, varquant = conf.Var.QUANT_SINGLE)
	a0 = conf.VarAssignment(
		valtree = conf.ValTreeNode_StringLiteral(conf_project, "gcc"),
		condtree = conf.CondTreeNode_True(),
		mode = conf.VarAssignment.MODE_APPEND,
		src = "default configuration"
	)


	cconf.addassignment(a0, conf=conf_project)
	variables["c"] = cconf

	targetlist = filetree.get_targets()
	tliterals = []

	for target in targetlist:
		d = target.get_dir_smname()
		t = target.get_smname()

		#create string literals for all target smnames
		tliterals.append(conf.ValTreeNode_StringLiteral(conf_project, t))

		if t not in conf.configs:
			cparents = [] #the parent directory TODO
			cdir = d #used as base for relative paths
			ctype = conf.Config.TYPE_DIR

			dconfig = conf.Config(name=d, conftype=ctype, parents=cparents, directory = cdir)

		else:
			dconfig = conf.configs[d]
			cdir = dconfig.directory



	variables["build"] = conf.Var(name='build', assscope=conf.Var.SCOPE_GLOBAL, valtype = conf.Var.TYPE_STRING)

	#tliterals is a list of conf string literals, so assign it to the ["build"]
	for tlit in tliterals:
		variables["build"].addassignment(
			conf.VarAssignment(
				valtree = tlit,
				condtree = conf.CondTreeNode_True(),
				mode = conf.VarAssignment.MODE_APPEND,
				src = "scanned target list"
			),
			conf=conf_project
		)
	#TODO: user configurable (=> exclude target from building)


	#iterate over all source files and create configs for them

	sourceslist = filetree.get_sources()

	for source in sourceslist:
		d = source.get_dir_smname()
		s = source.get_smname()

		if d not in conf.configs:
			cparents = [] #the parent directory
			cdir = d #used as base for relative paths
			ctype = conf.Config.TYPE_DIR

			dconfig = conf.Config(name=d, conftype=ctype, parents=cparents, directory = cdir)

		else:
			dconfig = conf.configs[d]
			cdir = dconfig.directory


		if s in conf.configs:
			raise Exception("duplicate entry for " + s + " in conf.configs")

		sparents = [dconfig]
		stype = conf.Config.TYPE_SRC

		sconfig = conf.Config(name=s, conftype=stype, parents=sparents, directory = cdir)



	print("===== variables: " + str(variables))
	print("===== end of variables")
	pprint.pprint(conf.configs)
	return variables, conf.configs



def main():
	print("fak u dolan")
	order = builder.BuildOrder()

	variables, confinfo = initvars1()
	order.fill(confinfo, variables)
	print("\n")
	pprint.pprint(order.filedict)
	print("\n")

	#use 4 threads
	m = builder.JobManager(4)
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
		raise Exception("sftmake builder exiting due to error")

if __name__ == "__main__":
	main()
