#!/usr/bin/python3

if not "assembled" in globals():
	from util import *

class Config:
	"""
	Holds metadata for a config:
	Its parent config, its associated directory, and its kind
	See __init__ documentation.
	Note that none of these parameters need to be unique, nor do they in
	"""

	BASE = EnumVal("Base configuration")
	DIR = EnumVal("Directory configuration")
	TARGET = EnumVal("Target configuration")
	SRC = EnumVal("Sourcefile configuration")
	SRCFORTARGET = EnumVal("Sourcefile- for- target configuration")

	def __init__(self, parents, directory, kind):
		"""
		parents:
			list of names of direct parent configurations
			for the absolute base config the list is empty,
			usually it has one element,
			for SRCFORTARGET configs it has two elements (the SRC and the TARGET config).
		directory: 
			the directory that this configuration is associated with
		rank:
			the rank of the configuration (BASE, DIR, TARGET, SRC, SRCFORTARGET)
		"""
		self.parents = parents
		self.directory = directory
		self.kind = kind

"""
Global dict that holds all variables
Key: Varname (String)
Val: Variable (Var object). Variables store values for all configs.
"""
variables = {}

"""
Global dict that holds metadata for all configs
Key: Confname (String, usually a path such as '^/libfoo.so')
Val: Metadata (Config object)
"""
confinfo = {}
""" 'default' is the absolute root configuration, and consists of the internal defaults """
confinfo["default"] = Config(parents = [], directory = '^', kind = Config.BASE)

#TODO this whole class
class Cond:
	"""	represents one condition """
	def create(condstr):
		""" abstract condition proxy factory singleton bean (not quite) """

		#read constr until operator sign
		#from that operator, decide which class to produce
		#give varname and condstr to the constructor of that class
		#return that class
		pass

	#abstract, must be implemented
	def check(self, conf, depends = OrderedSet()):
		raise NotImplementedError()

class Cond_Equals(Cond):
	def __init__(self, varname, val):
		self.val = val
		self.varname = varname

	def check(self, conf, depends = OrderedSet()):
		return (variables[varname].get(conf, depends) == val)

class Val:
	"""
	represents one variable value. it consists of:
	the actual string value
	a list of conditions, all of which must be met for the value to be applied to the result list
	a variable mode (see below)
	"""

	#append the value to the list. if it is already in the list, move it to the end.
	MODE_APPEND = EnumVal("Append")
	#delete the existing list, append the value
	MODE_SET = EnumVal("Set")
	#if it exists, remove the value from the existing list
	MODE_REMOVE = EnumVal("Remove")

	def __init__(self, string, conditions, mode):
		self.string = string
		self.conditions = conditions
		self.mode = mode
	
	def check_conds(self, conf, depends = OrderedSet()):
		"""
		check all conditions
		there might be circular dependencies, which could leed to infinite loops.
		we keep track of already-evaluated variables in 'depends'.
		also, conditions may evaluate differently depending on the active conf,
		so we need that as an argument as well.
		"""
		if conditions != None:
			for c in conditions:
				if not c.check(conf, depends):
					return False
		return True

class Var:
	"""
	one complete configuration variable, such as 'cflags'.
	stores a list of Vals for each conf
	"""

	TYPE_STRING = EnumVal("String")
	TYPE_PATH = EnumVal("Path")
	TYPE_INT = EnumVal("Int")

	def __init__(self, name, vartype = TYPE_STRING, single = False, defaultvals = []):
		"""
		varname:
			We need to know our own name for debugging purposes
		vartype:
			TYPE_STRING: Semantics-free strings
			TYPE_PATH: Strings are interpreted as paths relative to the directory of the conf
			TYPE_INT: If the String is not a valid Integer, a fatal error is raised
			List of strings: Only one of these is allowed.
		single:
			The variable is single-valued, i.e. when reading, instead of the list, only the
			newest entry is returned.
			A fatal error is raised if multiple values are added at once.
		defaultvals:
			The default values of the variable, i.e. a list of all values for the 'default' conf.
			After initialization, a Var stores only a value list for the default conf.
		"""
		self.name = name
		self.vartype = vartype
		self.single = single
		self.vals = {"default": defaultvals}

		#add ourselves to the global variable list
		variables[name] = self

	def addval(self, vallist, conf):
		""" adds the given value to the variable, for the given conf """

		#semantics stuff
		if self.vartype == VARTYPE_STRING:
			#VARTYPE_STRING has no semantics
			pass

		elif self.vartype == VARTYPE_PATH:
			#convert relative paths to smpaths
			val = smpathifrel(val, confinfo[conf].directory)

		#if vartype is an int, we parse it as such
		elif self.vartype == VARTYPE_INT:
			#check whether val is 
			try:
				int(val)
			except:
				raise Exception("Variable allows only integer values")

		#if vartype is a list, then val must be one of the list elements
		elif isinstance(self.vartype, list):
			if val not in self.vartype:
				raise Exception("Value must be one of " + str(self.vartype))
		else:
			raise Exception("Variable type unknown")

		#add val to the value list of conf
		if conf not in self.vals:
			self.vals[conf] = [val]
		else:
			self.vals[conf].append(val)

	def get(self, conf, depends = OrderedSet()):
		"""
		returns the variable value(s) for a certain configuration
		there might be circular dependencies, which could leed to infinite loops.
		we keep track of already-evaluated variables in 'depends'.
		"""
		if depends.append(self) == False:
			chain = self.name
			for v in depends:
				chain += ' -> ' + v.name
			raise Exception("Circular dependency resolving conditions: " + chain)

		result = OrderedSet()

		#for each val from each parent config
		for conf in confparenthyperres(conf):
			for val in self.vals.get(conf, []):
				#if condition of the value evaluates true, apply to result
				if val.check_conds(conf, depends):
					(mode, string) = val.get()
					if mode == VALMODE_APPEND:
						result.append(string)
					elif mode == VALMODE_SET:
						result.clear()
						result.append(string)
					elif mode == VALMODE_REMOVE:
						result.remove(string)
		
		if self.single:
			try:
				return result.newest()
			except:
				raise Exception("Single-val variable has no value")
		else:
			return result

def confparenthyperres(origin):
	"""
	returns all confs that the origin depends on, with the 'default' root configuration
	at the beginning and origin itself at the end
	"""
	result = OrderedSet()
	for parent in confinfo[origin].parents:
		result.update(confparenthyperres(parent))
	result.append(origin)
	return result

#all variables and their default configurations
Var('c', Var.TYPE_STRING, True, [
	Val(Cond.create("srcsuffix==cpp"), Val.MODE_APPEND, "g++"),
	Val(Cond.create("srcsuffix==c"  ), Val.MODE_APPEND, "gcc")
])

#the used source files
Var('srcs', Var.TYPE_PATH, False, [])
#etc... basically, type the variable list from documentation section 3
