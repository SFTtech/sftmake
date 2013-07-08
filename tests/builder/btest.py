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

import re
import pprint

import builder.builder

import util

from logger import *
from logger.levels import *

import conf
import conf.variable as variable
import conf.assignment as assignment

from conf.config import Config
from conf.variable import Var
from conf.assignment import Assignment
from conf.expr import Literal
from conf.boolexpr import CondTreeNode_True


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


def create_config(name, directory, ctype):
	#create config for target, will be in conf.configs[t]

	if name in conf.configs:
		raise Exception(name + " already has a configuration, you fail0r!")

	parent = directory

	if not parent in conf.configs:
		config_stack = []

		#fill the to-be-created config stack with missing configs
		while not parent in conf.configs:
			config_stack.append(parent)
			parent = util.parent_folder(parent)

			#this happens if the parent of ^ is searched
			if parent == '':
				break

		#after the loop above,
		#config_stack now looks like this:
		#[^/lol/folder/module, ^/lol/folder, ^/lol, ^]

		#easier creation by reversing:
		config_stack.reverse()
		#the reversed config_stack:
		#[^, ^/lol, ^/lol/folder, ^/lol/folder/module]

		#iterate over the config stack, we need the index
		for i in range(len(config_stack)):

			#the name of config we want to create:
			c = config_stack[i]

			if c == "^":
				#topmost parent of all the configs
				parent = "project"
			elif i < 1:
				#the config at beginning does not have a predecessor in the list
				# so we need to calculate the parent folder
				parent = util.parent_folder(c)
			else:
				#if existing, the parent of the current is stored in the list
				# before the current directory
				parent = config_stack[i-1]

			#create the config, name = c, and set the last parameter as follows:
			# directory = c as well, this is for the relativ path resolutions
			# of config entries (so lol.c is resolved to c/lol.c)
			parentconfs = [conf.configs[parent]]
			Config(c, Config.TYPE_DIR, parentconfs, c)

		#now we fetch the real newly created parent config of 'name'
		parent = config_stack.pop()

	#create the desired configuration node
	parentconf = [conf.configs[parent]]
	Config(name, ctype, parentconf, directory)



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
	conf_base = Config('^', Config.TYPE_DIR, [], '^')
	conf_main = Config('^/main.c', Config.TYPE_SRC, [conf_base], '^')
	conf_lib0 = Config('^/library0.c', Config.TYPE_SRC, [conf_base], '^')
	conf_lib1 = Config('^/library1.c', Config.TYPE_SRC, [conf_base], '^')
	conf_both = Config('^/both.c', Config.TYPE_SRC, [conf_base], '^')
	conf_lib = Config('^/liblol.so', Config.TYPE_TARGET, [conf_base], '^')
	conf_bin = Config('^/lolbinary', Config.TYPE_TARGET, [conf_base], '^')
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

	debug("starting creating variables by using dirscanner now")
	variables = dict()

	conf_project = Config(name="project", conftype=Config.TYPE_BASE, parents = [], directory='^')

	#TODO: this has to be generated by the dirscanner!
#	conf_root = conf.Config('^', conf.Config.TYPE_DIR, [conf_project], '^')
#	conf_main = conf.Config('^/main.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_lib0 = conf.Config('^/library0.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_lib1 = conf.Config('^/library1.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_both = conf.Config('^/both.c', conf.Config.TYPE_SRC, [conf_root], '^')
#	conf_lib = conf.Config('^/liblol.so', conf.Config.TYPE_TARGET, [conf_root], '^')
#	conf_bin = conf.Config('^/lolbinary', conf.Config.TYPE_TARGET, [conf_root], '^')


	cconf = Var(name='c', valtype=variable.VALTYPE_STRING, valcount = variable.VALCOUNT_LIST)

	a0 = Assignment(
		expressionlist = Literal(conf_project, "gcc"),
		condition = CondTreeNode_True(),
		mode = assignment.MODE_APPEND,
		src = "default configuration"
	)

	cconf.assign(conf_project, a0)
	variables["c"] = cconf


	import dirscanner, util

	projectpath = "./sftmake-testproject"

	filetree = dirscanner.smtree(rootpath=projectpath)
	project_smfile = filetree.get_root_smfile()

	new_root = filetree.get_root_smfile().directory
	message("===>  new smroot path: " + new_root)

	util.path.set_smroot(new_root)


	debug("--- executing smfiles")

	smfile_handlers = dict()
	for f in filetree.smfiles:
		fsmname = f.get_smname()
		debug("-> new smfile: " + fsmname)
		new_handler = f.create_handler()
		new_handler.run()
		smfile_handlers[fsmname] = new_handler

		#fill_vars(new_handler)

		debug("smfile handler created: \n" + str(new_handler))

	debug("--- done executing smfiles")

	#assign settings from root project smfile:
	#rootsmfile_handler = smfile_handlers[]


	#end assigning root smfile stuff

	#variable which contains a list of smnames, which are targets to be built
	variables["build"] = conf.Var(name='build', assscope=conf.Var.SCOPE_GLOBAL, valtype = conf.Var.TYPE_STRING)

	#variable to store which sources are used for a given target
	variables["use"] = conf.Var(name='use', assscope=conf.Var.SCOPE_CONF, valtype = conf.Var.TYPE_STRING)

	#get all defined targets by existing target smfiles
	targetlist = filetree.get_target_smfiles()

	debug("targets:\n" + str(list(targetlist)))

	#TODO: user configurable (=> exclude target from building)
	for target in targetlist:

		#type(target) == dirscanner.targetsmfile
		d = target.get_dir_smname()
		t = target.get_associated_smname()
		tsmhandler = target.get_smhandler()

		debug("** creating configurations for target " + t)

		#creates the inherit structure configuration (parents are set etc)
		create_config(name=t, directory=d, ctype=Config.TYPE_TARGET)

		variables["build"].addassignment(
			conf.VarAssignment(
				valtree = Literal(conf_project, t),
				condtree = conf.CondTreeNode_True(),
				mode = conf.VarAssignment.MODE_APPEND,
				src = "scanned targets"
			),
			conf=conf.configs[t]
		)

		#get the created smfile interpreter:
		sh = target.get_handler()

		#the smfile handler has data, means the smfile actually has contents
		if sh.data != None:

			#the smfile has set values for 'use'
			if 'use' in sh.data.data:

				#create entries for all to-be-used sources by this target
				for usesrc in sh.data.data['use']:
					usesrc = util.path.smpath(usesrc, relto=target.fileobj.get_dir_smname)

			variables["use"].addassignment(
				conf.VarAssignment(
					valtree = Literal(conf.configs[t], newuse),
					condtree = conf.CondTreeNode_True(),
					mode = conf.VarAssignment.MODE_APPEND,
					src = "scanned smfile content"
				),
				conf.configs[t]
			)



	variables["filelist"] = conf.Var(name='filelist', assscope=conf.Var.SCOPE_GLOBAL, valtype = conf.Var.TYPE_STRING)

	#get list of all sourcefiles from scanned filetree
	sourcelist = filetree.get_sources()

	debug("sourcelist:\n" + str(list(sourcelist)))

	#iterate over all source files and create configs for them
	#create "target uses" entries for usedby declarations
	#and ignore files not being used or having no configuration (e.g. srcsmfile or inline)
	#TODO ^ the above things

	#TODO: non-c-regex by project config smfile

	for source in sourcelist:
		d = source.get_dir_smname()
		s = source.get_smname() #TODO: this can reference the dirscaner.simple_file
		#TODO ^^^^
		#patternlist = variables["srcsuffix"].eval(s)
		#srcfileregex = "("
		#for p in patternlist:
		#	regex += p |
		#srcfileregex += ")"
		#if not re.match(r"\.(c|cpp)$", s):
		#	continue

		debug("** creating configurations for source " + s)

		create_config(s, d, Config.TYPE_SRC)

		#add this source to the global source file list
		variables["filelist"].addassignment(
			conf.VarAssignment(
				valtree = Literal(conf_project, s),
				condtree = conf.CondTreeNode_True(),
				mode = conf.VarAssignment.MODE_APPEND,
				src = "scanned sources"
			),
			conf=conf_project
		)


		#a file may have specifications in which targets it is used
		# -> usedby = [targets] in which source is used

		#TODO: get usedby assignments for this sourcefile!
		usedbytargets = []

		#TODO!!
		# move the file 'usedby' target definitions
		# into the target, so it 'uses' the source
		for target in usedbytargets:
			variables["usedby"].addassignment(
				conf.VarAssignment(
					valtree = Literal(conf_project, target),
					condtree = conf.CondTreeNode_True(),
					mode = conf.VarAssignment.MODE_APPEND,
					src = "usedby definitons"
				)
			)

	debug("----------------------- conv/var generation complete")

	if True:

		debug("-- variable ids:")
		for i in variables:
			debug(i + " : " + str(id(variables[i])))
		debug("-- end of variable ids")

		debug("===== variables:")
		debug(str(variables))
		debug("===== end of variables")

		debug("===== configs:")
		debug(pprint.pformat(conf.configs))
		debug("===== end of configs")


	return variables, conf.configs



def main():
	#import sys
	#dirty redirection of python error messages to logger
	#sys.stderr.write = lambda message: error(message)

	important("fak u dolan")
	order = builder.builder.BuildOrder()

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