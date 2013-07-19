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
import util.path

from logger import *
from logger.levels import *

import conf
import conf.variable as variable
import conf.assignment as assignment

from conf.config import Config
from conf.variable import Var
from conf.assignment import Assignment
import conf.expr as expr
import conf.boolexpr as boolexpr


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
			parent = util.path.parent_folder(parent)

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
				parent = util.path.parent_folder(c)
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



def initvars1():
	'''
	approach of creating the config via python by using conf infrastructure
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


	cconf = Var(name='c', valtype=variable.VALTYPE_STRING, valcount = variable.VALCOUNT_SINGLE)

	a0 = Assignment(
		expressionlist = expr.Literal(conf_project, "gcc"),
		condition = boolexpr.CondTreeNode_True(),
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
	variables["build"] = variable.Var(name='build', assignmentscope=variable.ASSIGNMENTSCOPE_GLOBAL)

	#variable to store which sources are used for a given target
	variables["use"] = variable.Var(name='use')

	#get all defined targets by existing target smfiles
	targetlist = filetree.get_target_smfiles()

	debug("targets:\n" + str(list(targetlist)))

	#TODO: user configurable (=> exclude target from building)
	for target in targetlist:

		#type(target) == dirscanner.targetsmfile
		d = target.get_dir_smname()
		t = target.get_associated_smname()
		tsmhandler = target.get_handler()

		debug("** creating configurations for target " + t)

		#creates the inherit structure configuration (parents are set etc)
		create_config(name=t, directory=d, ctype=Config.TYPE_TARGET)

		variables["build"].assign(
			conf=conf.configs[t],
			assignment = assignment.Assignment(
				expressionlist = expr.Literal(conf_project, t),
				condition = boolexpr.CondTreeNode_True(),
				mode = assignment.MODE_APPEND,
				src = "scanned targets"
			)
		)

		#get the created smfile interpreter:
		sh = target.get_handler()

		#the smfile handler has data, means the smfile actually has contents
		if sh.data != None:

			#the smfile has set values for 'use'
			if 'use' in sh.data.data:

				#create entries for all to-be-used sources by this target
				for usesrc in sh.data.data['use']:
					#TODO: create used src path relative to target directory
					#usesrc = util.path.smpath(usesrc, relto=target.get_dir_smname())
					usesrc = util.path.smpath(usesrc)

					variables["use"].assign(
						conf = conf.configs[t],
						assignment = assignment.Assignment(
							expressionlist = expr.Literal(conf.configs[t], usesrc),
							condition = boolexpr.CondTreeNode_True(),
							mode = assignment.MODE_APPEND,
							src = "scanned smfile content"
						)
					)



	variables["filelist"] = variable.Var(name='filelist', assignmentscope=variable.ASSIGNMENTSCOPE_GLOBAL)

	variables["srcsuffix"] = variable.Var(name='srcsuffix')

	#only allow source files ending with .c
	variables["srcsuffix"].assign(
		conf = conf.configs['project'],
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], r"\.c"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["cflags"] = variable.Var(name='cflags')

	variables["cflags"].assign(
		conf = conf.configs['project'],
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "-pedantic"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["ldflags"] = variable.Var(name='ldflags')

	variables["ldflags"].assign(
		conf = conf.configs['project'],
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "-llol"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["prebuild"] = variable.Var(name='prebuild')

	variables["prebuild"].assign(
		conf = conf.configs['project'],
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "echo rein"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["postbuild"] = variable.Var(name='postbuild')

	variables["postbuild"].assign(
		conf = conf.configs['project'],
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "echo raus"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["autodepends"] = variable.Var(name='autodepends', valcount = variable.VALCOUNT_SINGLE)

	variables["autodepends"].assign(
		conf = conf.configs['project'],
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "MD"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)

	variables["loglevel"] = variable.Var(name='loglevel', valcount = variable.VALCOUNT_SINGLE)

	variables["loglevel"].assign(
		conf = conf.configs['project'],
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "8"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["objdir"] = variable.Var(name='objdir', valtype=variable.VALTYPE_STRING, valcount = variable.VALCOUNT_SINGLE)

	variables["objdir"].assign(
		conf = conf.configs['project'],
		assignment = Assignment(
			expressionlist = expr.Literal(conf_project, "^/.objs"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "default configuration"
		)
	)



	variables["depends"] = variable.Var(name='depends')

	#get list of all sourcefiles from scanned filetree
	sourcelist = filetree.get_sources()

	debug("---- creating list of sources")
	debug("FILELIST:\n" + str(list(sourcelist)))

	#iterate over all source files and create configs for them
	#create "target uses" entries for usedby declarations
	#and ignore files not being used or having no configuration (e.g. srcsmfile or inline)

	for source in sourcelist:
		d = source.get_dir_smname()
		s = source.get_smname() #TODO: this can reference the dirscaner.simple_file

		#get the list of all suffixes currently enabled
		patternlist = variables["srcsuffix"].eval(conf.configs[d])

		srcfileregex = r".*("
		start = True
		for p in patternlist:
			srcfileregex += p + (r"|" if not start else "")
			start = False
		srcfileregex += r")$"

		if not re.match(srcfileregex, s):
			debug("skipped -> " + s + ", not matching " + srcfileregex)
			continue

		else:
			debug("using source -> " + s + ", matching " + srcfileregex)

		debug("** creating configurations for source " + s)

		create_config(s, d, Config.TYPE_SRC)

		print("lol")

		#add this source to the global source file list
		variables["filelist"].assign(
			conf=conf_project,
			assignment = assignment.Assignment(
				expressionlist = expr.Literal(conf_project, s),
				condition = boolexpr.CondTreeNode_True(),
				mode = assignment.MODE_APPEND,
				src = "scanned sources"
			)
		)


		#a file may have specifications in which targets it is used
		# -> usedby = [targets] in which source is used

		#TODO: get usedby assignments for this sourcefile!
		usedbytargets = []

		#TODO!!
		# move the file 'usedby' target definitions
		# into the target, so it 'uses' the source
		for target in usedbytargets:
			variables["usedby"].assign(
				conf = "asdf TODO",
				assignment = assignment.Assignment(
					expressionlist = expr.Literal(conf_project, target),
					condition = boolexpr.CondTreeNode_True(),
					mode = assignment.MODE_APPEND,
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
		debug(pprint.pformat(variables))
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
	debug(pprint.pformat(order.filedict))

	#use 4 threads
	m = builder.builder.JobManager(4)
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
		important("sftmake builder shutting down regularly")
	else:
		raise Exception("sftmake builder exiting due to error")
