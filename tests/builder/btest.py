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

import dirscanner
from dirscanner import *




#TODO: make this recursive (create config called again for parents etc)
def create_config(name, parent, ctype):
	#create config for target, will be in conf.configs[t]

	if name in conf.configs:
		raise Exception("'" + name + "' already has a configuration, you fail0r!")

	if name[0] != "^":
		raise Exception("config name '" + name + "' does not start with ^")

	debug("recursively creating configuration for "+ str(ctype) + " '" + name + "' parent(" + parent + ")")

	config_stack = []

	#fill the to-be-created config stack with missing configs
	#create a list of parent config names first
	while not parent in conf.configs:
		config_stack.append(parent)
		parent = util.path.parent_folder(parent)

		#this happens if the parent of ^ is searched
		if parent == 'project':
			break

	#after the loop above,
	#config_stack now looks like this:
	#[^/lol/folder/module, ^/lol/folder, ^/lol, ^]
	#the config 'project' should normally already exist

	#easier creation by reversing:
	config_stack.reverse()
	#the reversed config_stack:
	#[^, ^/lol, ^/lol/folder, ^/lol/folder/module]

	confnumber = len(config_stack)

	debug("creating " + str(confnumber) + " parent configuration(s) for '" + str(name) + "':")
	debug("parents: " + str(config_stack))

	#iterate over the config stack, we need the index
	for i in range(confnumber):

		#the name of config we want to create:
		c = config_stack[i]

		if c == "^":
			#topmost parent of all the configs, was already create for root smfile
			iparent = "project"
		elif i < 1:
			#the config at beginning does not have a predecessor in the list
			# so we need to calculate the parent folder
			iparent = util.path.parent_folder(c)
		else:
			#if existing, the parent of the current is stored in the list
			# before the current directory
			iparent = config_stack[i-1]

		#create the config, name = c, and set the last parameter as follows:
		# directory = c as well, this is for the relativ path resolutions
		# of config entries (so lol.c is resolved to c/lol.c)
		iparentconf = [conf.configs[iparent]]
		debug("creating dir parent config for " + str(name) + ": " + str(c))
		Config(c, Config.TYPE_DIR, iparentconf, iparent)

	parentconf = [conf.configs[parent]]

	debug("creating requested config '" + name + "' (" + str(ctype) + ") now.")
	#create the desired configuration nodes
	return Config(name, ctype, parentconf, parent)



def initvars1():
	'''
	approach of creating the config via python by using conf infrastructure
	'''

	debug("generating dynamic configuration using dirscanner")
	variables = dict()

	#create all required variables (these are directly used by sftmake)
	#user variables will be created on demand

	conf_project = Config(name="project", conftype=Config.TYPE_BASE, parents = [], directory='^')

	variables["c"] = Var(name='c', valtype=variable.VALTYPE_STRING, valcount = variable.VALCOUNT_SINGLE)
	variables["build"] = variable.Var(name='build', assignmentscope=variable.ASSIGNMENTSCOPE_GLOBAL)
	variables["use"] = variable.Var(name='use')
	variables["srcsuffix"] = variable.Var(name='srcsuffix')
	variables["cflags"] = variable.Var(name='cflags')
	variables["ldflags"] = variable.Var(name='ldflags')
	variables["prebuild"] = variable.Var(name='prebuild')
	variables["postbuild"] = variable.Var(name='postbuild')
	variables["autodepends"] = variable.Var(name='autodepends', valcount = variable.VALCOUNT_SINGLE)
	variables["loglevel"] = variable.Var(name='loglevel', valcount = variable.VALCOUNT_SINGLE)
	variables["objdir"] = variable.Var(name='objdir', valtype=variable.VALTYPE_STRING, valcount = variable.VALCOUNT_SINGLE)
	variables["depends"] = variable.Var(name='depends')


	#assign default values for the mandatory variables
	variables["c"].assign(
		conf = conf_project,
		assignment = Assignment(
			expressionlist = expr.Literal(conf_project, "gcc"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "default configuration"
		)
	)


	#only allow source files ending with .c
	variables["srcsuffix"].assign(
		conf = conf_project,
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], r"\.c"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["cflags"].assign(
		conf = conf_project,
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "-pedantic"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["prebuild"].assign(
		conf = conf_project,
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "echo rein"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["postbuild"].assign(
		conf = conf_project,
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "echo raus"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["autodepends"].assign(
		conf = conf_project,
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "no"), #"MD"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["loglevel"].assign(
		conf = conf_project,
		assignment = assignment.Assignment(
			expressionlist = expr.Literal(conf.configs['project'], "8"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "hardcoded in btest"
		)
	)


	variables["objdir"].assign(
		conf = conf_project,
		assignment = Assignment(
			expressionlist = expr.Literal(conf_project, "^/.objs"),
			condition = boolexpr.CondTreeNode_True(),
			mode = assignment.MODE_APPEND,
			src = "default configuration"
		)
	)


	projectpath = "./sftmake-testproject"

	#scan the project root with the dirscanner.py:
	filetree = smtree(rootpath=projectpath)
	project_smfile = filetree.get_root_smfile()

	new_root = filetree.get_root_smfile().directory
	message("===>  new smroot path: " + new_root)

	util.path.set_smroot(new_root)


	debug("--- executing smfiles")

	filetree.execute_smfiles()

	debug("--- done executing smfiles")


	#get all defined smfiles/inlineconfs found by the dirscanner
	smfilelist = filetree.get_smfiles()

	debug("Processing these smfiles: \n" + str("".join( ( str(sf) for sf in smfilelist ) )))

	#TODO: user configurable targets (=> exclude target from building)
	for smfile in smfilelist:

		dn = smfile.get_dir_smname()
		an = smfile.get_associated_smname()
		sn = smfile.get_smname()

		#get the created smfile interpreter:
		smhandler = smfile.get_handler()

		#create configurations with smfile type specific actions (like adding to build list etc)

		if get_filetype(smfile) == FILE_SRCSMFILE:
			debug("** creating configurations for source " + an)
			cfg = create_config(name=an, parent=dn, ctype=Config.TYPE_SRC)

		elif get_filetype(smfile) == FILE_TARGETSMFILE:
			debug("** creating configurations for target " + an)
			cfg = create_config(name=an, parent=dn, ctype=Config.TYPE_TARGET)

			#add the target to the list of buildable elements
			variables["build"].assign(
				conf=cfg,
				assignment = assignment.Assignment(
					expressionlist = expr.Literal(conf_project, an),
					condition = boolexpr.CondTreeNode_True(),
					mode = assignment.MODE_APPEND,
					src = "scanned targets"
				)
			)

		elif get_filetype(smfile) == FILE_DIRSMFILE:
			debug("** creating configurations for directory " + an)
			dn = util.path.parent_folder(dn)
			cfg = create_config(name=an, parent=dn, ctype=Config.TYPE_DIR)

		elif get_filetype(smfile) == FILE_INLINESMFILE:
			debug("** creating configurations for source " + an + " (inlined)")
			cfg = create_config(name=an, parent=dn, ctype=Config.TYPE_SRC)

		elif get_filetype(smfile) == FILE_ROOTSMFILE:
			debug("** configuration for project root already created, skipping")
			cfg = conf_project

		else:
			raise Exception("unknown smfile type, wtf?")

		#the smfile handler has data, means the smfile actually has contents
		if smhandler.data != None:

			#iterate over all settings defined in the smfile (e.g. use, depends, type etc)
			for setting in smhandler.data.data:

				#create the variable if it is not yet existing
				if not setting in variables:
					debug("creating variable '" + setting + "'")
					variables[setting] = variable.Var(name=setting)

				#development support: disable all unknown variables
				if setting not in ['use', 'c', 'ldflags', 'cflags', 'depends']:
					message("ignoring your setting for '" + str(setting) + "' in " + repr(smfile) + " for now.")
					continue

				#the value which the user has set in the smfile
				userval = smhandler.data.data[setting]

				#the type of the current variable, which the user has set in the smfile
				vtype = type(userval)


				if type(userval) != list:
					userval = [userval]


				#switch by type of this var (predefined mandatory ones) (dir, int, string)
				#and by valcount (single, list)
				#create used src path relative to target directory (if type dir)
				#(create var for v if not yet existing (for user created vars))

				expectedtype = variables[setting].valtype

				#iterate over all assignments the user made for this smfile
				for assign_val in userval:

					if expectedtype == variable.VALTYPE_INT:
						val = int(assign_val)

					elif expectedtype == variable.VALTYPE_PATH:
						#make path relative to the folder where the smfile was found
						val = util.path.smpath(assign_val, relto=dn)

					elif expectedtype == variable.VALTYPE_STRING:
						#add a string value, simple and easy...
						val = str(assign_val)

					debug("-- assigning '" + val + "' to variable '" + setting + "' for config " + repr(cfg))

					#TODO: expressionlist?
					#TODO: conditions!
					#TODO: mode!
					#TODO: src!!!!
					variables[setting].assign(
						conf = cfg,
						assignment = assignment.Assignment(
							expressionlist = expr.Literal(cfg, val),
							condition = boolexpr.CondTreeNode_True(),
							mode = assignment.MODE_APPEND,
							src = "set in " + repr(smfile)
						)
					)


		else:
			#the smfile has no data stored
			pass

	debug("=== finished creating configs for smfiles")

	message(conf_project.treeview())

	debug("======== iterating over all source files")

	#calculate the list of all needed sources, by examining all "use" settings of targets
	targetlist = variables["build"].eval(conf_project)
	debug("list of all targets: " + str(targetlist.tolist()))

	needed_sources_smnames = set()
	for t in targetlist:
		needed_sources_smnames = needed_sources_smnames | set(variables["use"].eval(conf.configs[t]).tolist())

	all_sources = filetree.get_sources()
	debug("dirscanner found these sources:\n" + str(all_sources))

	#we now overlay the key names (needed_sources) with the keys of all_sources
	#to only keep the needed elements of all_sources
	#TODO: this surely can be boosted somehow...
	needed_sources = set()
	for source in all_sources:
		if source.get_smname() in needed_sources_smnames:
			needed_sources.add(source)

	#this calculated a set of sources which will be built sometime.
	debug("found needed sources: " + str(needed_sources))

	for source in needed_sources:
		#iterate over all source files and create configs for them
		#create "target uses" entries for usedby declarations
		#and ignore files not being used or having no configuration (e.g. srcsmfile or inline)

		sn = source.get_smname()
		dn = source.get_dir_smname()

		#only create the source config if it has no config yet
		if sn not in conf.configs:
			debug("** creating configurations for source " + sn)
			create_config(sn, dn, Config.TYPE_SRC)

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
					expressionlist = expr.Literal(cfg, target), #TODO: this must be the project configuration
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

		#debug("===== variables:")
		#debug(pprint.pformat(variables))
		#debug("===== end of variables")

		debug("===== configs:")
		debug(conf.configs["project"].treeview())
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
	debug("order filedict =\n" + pprint.pformat(order.filedict))

	debug(order.text())

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
		return True
	else:
		error("sftmake builder exiting due to error")
		return False
