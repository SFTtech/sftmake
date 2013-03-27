#!/usr/bin/python3

if not "assembled" in globals():
	from util import *

class Config:
	BASE = EnumVal("Conf type: Base")
	DIR = EnumVal("Conf type: Directory")
	TARGET = EnumVal("Conf type: Target")
	SRC = EnumVal("Conf type: Sourcefile")
	SRCFORTARGET = EnumVal("Conf type: Sourcefile- for target")

	def __init__(self, parents, conftype):
		"""
		parents:
			list of names of direct parent configurations
			for the absolute base config 'default', the list is empty,
			usually it has one element,
			for SRCFORTARGET configs it has two elements (the SRC and the TARGET config).
		conftype:
			the type of the configuration (BASE, DIR, TARGET, SRC, SRCFORTARGET)
		"""
		self.parents = parents
		self.conftype = conftype

"""
Global dict that holds all variables
Key: Varname (String)
Val: Variable (Var object). Variables store values for all configs.
"""
variables = {}
"""
Global dict that holds metadata for all configs. Required for confparenthyperres.
Key: Confname (String, usually a path such as '^/libfoo.so')
Val: Metadata (Config object)
"""
configs = {}
"""
'default' is the absolute root configuration, and consists of the internal defaults
"""
configs["default"] = Config(parents = [], conftype = Config.BASE)

def confparenthyperres(origin):
	"""
	Returns all confs that the origin conf depends on,
	with the 'default' root configuration at the beginning and origin itself at the end.
	"""
	result = OrderedSet()
	for parent in configs[origin].parents:
		result.update(confparenthyperres(parent))
	result.append(origin)
	return result

#TODO subclasses
class CondTreeNode:
	def check(self, conf, depends):
		"""
		checks whether the condition is true.

		conf:
			the configuration for which we are checking
		depends:
			for detecting circular variable dependencies (and thus infinite loops)
		"""
		#not implemented in abstract base class
		raise NotImplementedError()

class CondTreeNode_HasVals(CondTreeNode):
	"""
	checks whether a variable contains all vals from the given valtrees
	"""
	def __init__(self, varname, valtrees):
		self.varname = varname
		self.valtrees = valtrees

	def check(self, conf, depends):
		requiredvals = set()
		for valtree in self.valtreees:
			requiredvals |= set(valtree.eval())
		varvals = set(variables[self.varname].get(conf, depends))
		return requiredvals < varvals


#TODO subclasses for function calls etc
class ValTreeNode:
	def eval(self, conf, depends):
		"""
		returns a list of strings (usually exactly one) that is the evaluated value tree.

		conf:       the configuration for which we are evaluating
		depends:    for detecting circular variable dependencies (and thus infinite loops)
		"""
		#not implemented in the abstract base class
		raise NotImplementedError()

class ValTreeNode_Empty:
	"""
	contains no data
	"""
	def eval(self, conf, depends):
		return []

class ValTreeNode_StringLiteral:
	"""
	contains one string literal
	"""
	def __init__(self, val):
		self.val = val
	
	def eval(self, conf, depends):
		return [val]

class ValTreeNode_Path:
	"""
	has children valtreenodes, and assumes that all of the strings returned by those nodes are paths.
	converts them to smpaths if they are no absolute paths.

	children:
		the children nodes
	directory:
		relative paths are assumed to be relative to this directory
	"""
	def __init__(self, children, directory):
		self.children = children
		self.directory = directory
	
	def eval(self, conf, depends):
		result = []
		for child in self.children:
			for string in child.eval():
				result.append(smpathifrel(string))
		return result

class VarAssignment:
	"""
	represents one list of values that are assigned to a variable.

	valtrees:
		the parsed value trees. in the simplest case, just a list of string literals,
		but it might involve function calls etc.
	conditions:
		a list of conditions that need to be fulfilled for the assignment to take effect
	mode:
		if the assignment takes effect, it might do so in a multitude of ways:
			appending the vals to a list (+=),
			replacing the list (=),
			removing from the list (-=)
	src:	a string that describes the source of this assignment for use in error messages,
		e.g. '^/smfile, line 80' or 'argv[3]'
	"""

	#append the value to the list. if it is already in the list, move it to the end.
	MODE_APPEND = EnumVal("Assignment mode: Append")
	#delete the existing list, append the value
	MODE_SET = EnumVal("Assignment mode: Set")
	#if it exists, remove the value from the existing list
	MODE_REMOVE = EnumVal("Assignment mode: Remove")

	def __init__(self, valtrees, conditions, mode, src):
		self.valtrees = valtrees #list of ValTreeNode
		self.conditions = conditions #list of 
		self.mode = mode
		self.src = src
	
	def check_conds(self, conf, depends):
		"""
		check all conditions
		there might be circular dependencies, which could lead to infinite loops.
		we keep track of already-evaluated variables in 'depends'.
		also, conditions may evaluate differently depending on the conf path,
		so we need that as an argument as well.
		"""
		for cond in conditions:
			if not cond.check(conf, depends):
				return False
		return True
	
	def eval(self, conf, depends):
		"""
		evaluate the valtrees, reducing them to a list of strings.
		conf and depends are required since evaluation might invoke other variables.
		"""
		result = []
		for valtree in self.valtrees:
			result += valtree.eval()
		return result

class Var:
	"""
	One complete configuration variable, such as 'cflags'. Stores lists of VarAssignments for each conf.

	valtype:
		the kind of information that is carried in the variable values.
		may be STRING (simple string), PATH (strings will be auto-converted to smpaths),
		or INT (assignment will fail for non-integer strings)
	varquant:
		specifies whether the variable stores only a single value (SINGLE),
		or a list of multiple values (MULTI)
	assscope:
		specifies whether assignments affect the var only for the conf where they were assigned (SCOPE_CONF),
		or if the concept of confs does not apply to this variable at all (SCOPE_GLOBAL).
		most variables will be SCOPE_CONF.
	"""

	TYPE_STRING = EnumVal("Value type: String")
	TYPE_PATH = EnumVal("Value type: Path")
	TYPE_INT = EnumVal("Value type: Int")

	QUANT_SINGLE = EnumVal("Variable Quantifier: Single")
	QUANT_MULTI = EnumVal("Variable Quantifier: Multi")

	SCOPE_CONF = EnumVal("Scope: Conf")
	SCOPE_GLOBAL = EnumVal("Scope: Global")

	def __init__(self, name, valtype = TYPE_STRING, varquant = QUANT_MULTI, assscope = SCOPE_CONF, defaultassignments = []):
		"""
		defaultassignments:
			A list of VarAssignments, used as default (root) conf for this variable
		"""
		self.name = name
		self.valtype = valtype
		self.varquant = varquant
		self.assscope = assscope
		self.assignments = {"default": defaultassignments}

		#add ourselves to the global variable list
		variables[name] = self

	def addass(self, assignment, conf):
		"""
		adds the given VarAssignment to the variable, for the given conf
		assignment:
			the VarAssignment
		conf:
			the conf (as a string)
		"""

		if conf not in self.vals:
			self.assignments[conf] = [assignment]
		else:
			self.assignments[conf].append(assignment)

	def get(self, conf, depends = OrderedSet()):
		"""
		returns the string values of the var, for a certain conf.
		conf:
			the conf, as a string
		depends:
			when getting the string values of the variable, we might need
			other variables as dependencies (for conditions, etc...).
			that way, circular dependencies and thus infinite loops may evolve,
			which we need to detect this way.
		"""

		#check if self is already in depends
		if depends.append(self) == False:
			#if yes, raise exception.
			chain = self.name
			for v in depends:
				chain += ' -> ' + v.name
			raise Exception("Circular variable dependency: " + chain)

		#prepare set of result strings
		result = OrderedSet()

		#iterate over all assignments in all parent configs
		for conf in confparenthyperres(conf):
			for assignment in self.assignments.get(conf, []):
				#first, check the condition
				if not assignment.check_conds(conf, depends):
					continue

				assignment_strings = assignment.eval(conf, depends)
				
				#check if all assignment strings match the valtype
				if self.valtype == TYPE_STRING or self.valtype == TYPE_PATH:
					#no special requirements; path strings are already processed at an earlier point
					pass
				elif self.valtype == TYPE_INT:
					for string in assignment_strings:
						int(string)
				elif type(self.valtype) == list:
					for string in assignment_strings:
						if string not in self.valtype:
							raise Exception("Value must be one of " + str(self.valtype))
				else:
					raise Exception("Unknown value type: " + repr(self.valtype))

				#apply assignment strings to result, depending on assignment mode
				if assignment.mode == VarAssignment.MODE_APPEND:
					for string in assignment_strings:
						result.append(string)
				elif assignment.mode == VarAssignment.MODE_SET:
					result.clear()
					for string in assignment_strings:
						result.append(string)
				elif assignment.mode == VarAssignment.MODE_REMOVE:
					for string in assignment_strings:
						result.remove(string)
		
		if self.varquant == QUANT_SINGLE:
			try:
				return result.newest()
			except:
				raise Exception("Single-quantified variable has no value")
		elif self.varquant == QUANT_MULTI:
			return result
		else:
			raise Exception("Unknown variable quantifier")

#all variables and their default configurations
#TODO invalid syntax by now
Var('c', Var.TYPE_STRING, True, [
	Val(Cond.create("srcsuffix==cpp"), Val.MODE_APPEND, "g++"),
	Val(Cond.create("srcsuffix==c"  ), Val.MODE_APPEND, "gcc")
])

#TODO invalid syntax as well
#the used source files
Var('srcs', Var.TYPE_PATH, False, [])
#etc... basically, type the variable list from documentation section 3
