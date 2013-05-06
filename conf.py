#!/usr/bin/python3
import itertools

if not "assembled" in globals():
	from util import *

class Config:
	"""
	other than the name might suggest, this class holds no actual config data.
	it merely manages metadata for configurations such as their name, and their parent configurations.
	actual config data is stored by the Var objects

	name
		example conf names:

		default
		args
		^
		^/libsft
		^/main.cpp
		^/libsft:^/main.cpp

	conftype
		One of
			TYPE_BASE (the 'default' and 'args' configs),
			TYPE_DIR,
			TYPE_TARGET,
			TYPE_SRC,
			TYPE_SRCFORTARGET

	parents
		list of pointers to direct parent configurations

		example parent lists:

		base:default
			[]
		dir:^
			[base:args]
		srcfortarget:^/libsft:^/main.cpp
			[target:^/libsft, src:^/main.cpp]

	directory
		the directory relative to which relative paths sould be interpreted

		example directories:

		base:default
			^
		dir:^
			^
		dir:^/tests
			^/tests
		src:^/tests/main.cpp
			^/tests
		srcfortarget:^/tester:^/tests/main.cpp
			^/tests
	"""

	TYPE_BASE = EnumVal("Base config")
	TYPE_DIR = EnumVal("Directory config")
	TYPE_TARGET = EnumVal("Target config")
	TYPE_SRC = EnumVal("Sourcefile config")
	TYPE_SRCFORTARGET = EnumVal("Source- for- target config")

	def __init__(self, name, conftype, parents, directory):
		self.name = name
		self.conftype = conftype
		self.parents = parents
		self.directory = directory
		configs[name] = self

	def __repr__(self):
		result = repr(self.conftype) + ": " + self.name + " (dir: " + self.directory
		result += "; parents: " + repr([paren.name for paren in self.parents]) + ")"
		return result

	def parenthyperres(self):
		"""
		Returns whole inheritance list for the conf,
		starting with the most base conf 'default', and ending with self.
		"""
		result = OrderedSet()
		for parent in self.parents:
			result.update(parent.parenthyperres())
		result.append(self)
		return result

class CondTreeNode:
	"""
	represents one condition tree node.
	assignment conditions consist of a list of condition tree nodes, which may in return have more
	condition tree nodes as children.
	consider the example: cflags[$mode==dbg] += -g
		the condition is one CondTreeNode which checks whether $mode equals dbg.
	consider the example: cflags[$mode==dbg || $mode==dbgo] += -g
		the condition is one CondTreeNode of type 'or', which has two children.
		one child checks whether $mode equals dbg, and the other one checks wheter $mode equals dbgo
	"""

	def eval(self, evalconf, depends):
		"""
		evaluates whether the condition is met.

		evalconf
			the conf for which we are evaluating
		depends
			for detecting circular variable dependencies (and thus infinite loops)
		"""
		#not implemented in abstract base class
		raise NotImplementedError()

class CondTreeNode_Not(CondTreeNode):
	"""
	logic 'not' of one condition
	"""
	def __init__(self, condtree):
		self.condtree = condtree

	def __repr__(self):
		return "not(" + repr(self.condtree) + ")"

	def eval(self, evalconf, depends):
		return not self.condtree.eval(evalconf, depends)

class CondTreeNode_And(CondTreeNode):
	"""
	logic 'and' of multiple conditions
	evaluation stops when the first false condition is encountered
	"""
	def __init__(self, condtrees):
		self.condtrees = condtrees

	def __repr__(self):
		return "and(" + repr(self.condtrees) + ")"

	def eval(self, evalconf, depends):
		for c in self.condtrees:
			if not c.eval(evalconf, depends):
				return False

		return True

class CondTreeNode_Or(CondTreeNode):
	"""
	logic 'or' of multiple conditions
	evaluation stops when the first true condition is encountered
	"""
	def __init__(self, condtrees):
		self.condtrees = condtrees

	def __repr__(self):
		return "or(" + repr(self.condtrees) + ")"

	def eval(self, evalconf, depends):
		for c in self.condtrees:
			if c.eval(evalconf, depends):
				return True

		return False

class CondTreeNode_Xor(CondTreeNode):
	"""
	logic 'xor' of multiple conditions
	true if an odd number of conditions evaluate to true
	all conditions are evaluated
	"""
	def __init__(self, condtrees):
		self.condtrees = condtrees

	def __repr__(self):
		return "xor(" + repr(self.condtrees) + ")"

	def eval(self, evalconf, depends):
		result = False

		for c in self.condtrees:
			if c.eval(evalconf, depends):
				result = not result

		return result

class CondTreeNode_Implies(CondTreeNode):
	"""
	logic 'implies' of two conditions
	true if the left condition is false, or if left and right are true
	the right condition is not evaluated if the left condition is false
	"""
	def __init__(self, condtreel, condtreer):
		self.condtreel = condtreel
		self.condtreer = condtreer

	def __repr__(self):
		return "(" + repr(self.condtreel) + ") -> (" + repr(self.condtreer) + ")"

	def eval(self, evalconf, depends):
		return not condtreel.eval(evalconf, depends) or condtreer.eval(evalconf, depends)

class CondTreeNode_Leaf(CondTreeNode):
	"""
	abstract class that represents a condtree leaf node,
	i.e. one that actually checks a condition,
	such as 'equals', 'greater than', 'subset', ...
	"""
	def __init__(self, leftvals, rightvals):
		"""
		leftvals
			ValTreeNode for the vals left of the operator
		rightvals
			ValTreeNode for the vals right vor the operator
		"""
		self.leftvals = leftvals
		self.rightvals = rightvals

	def __repr__(self):
		return "(" + repr(self.leftvals) + " " + self.operator + " " + repr(self.rightvals) + ")"

	def evallr(self, evalconf, depends):
		"""
		evaluate the left and right valtrees
		used by the eval() methods
		"""
		left = self.leftvals.eval(evalconf, Var.TYPE_STRING, depends)
		right = self.rightvals.eval(evalconf, Var.TYPE_STRING, depends)
		return left, right

	def select(operator):
		"""
		selects the appropriate CondTreeNode leaf type, from the given operator
		"""
		if operator in ["==", "=", "equals", "eq"]:
			return CondTreeNode_Leaf_Equals
		elif operator in ["subset of", "subsumes"]:
			return CondTreeNode_Leaf_SubSet
		else:
			raise Exception("Unknown condition operator")

class CondTreeNode_Leaf_Equals(CondTreeNode_Leaf):
	"""
	checks whether the left and right expressions are equal
	note that in the current implementation, this also checks whether the order is identical.
	maybe introduce a '===' operator for that? TODO
	"""
	operator = "=="

	def check(self, evalconf, depends):
		leftvals, rightvals = self.evallr(evalconf, depends)
		return leftvals == rightvals

class CondTreeNode_Leaf_SubSet(CondTreeNode_Leaf):
	"""
	checks whether the left expression is a subset of the right expression
	does not take order into consideration
	"""
	operator = "subset of"

	def check(self, evalconf, depends):
		leftvals, rightvals = self.evallr()
		return set(leftvals) < set(rightvals)

#TODO obviously we need more Leaf nodes

class ValTreeNode:
	"""
	similar to CondTreeNode, represents one value tree node.
	assignment values consist of a list of val tree nodes, which may themselves have more
	value tree nodes as children.
	consider the example: cflags += -g
		the values are a single ValTreeNode of type Literal, with value '-g'.
	consider the example: cflags += -g, -Wall, $(shell ls), $lflags, ${${mode}}
		the values are four ValTreeNodes:
		one literal, '-g'
		one literal, '-Wall'
		one function call, function name is a literal 'shell', function args is one literal 'ls'
		one variable call, variable name is a literal 'lflags'
		one variable call, variable name is a variable call, variable name is a literal 'mode'
	"""

	def __init__(self, conf):
		"""
		conf
			configuration where the ValTreeNode was declared
		"""
		self.conf = conf

	def eval(self, evalconf, valtype, depends):
		"""
		evaluates this node and returns the result values as a list of strings

		evalconf
			configuration for which we are evaluating
			needed e.g. when calling variables, or evaluating conditions
		valtype
			type that we expect the eval() to return (STRING, PATH, INT, ...)
		depends
			for detecting circular variable dependencies (and thus infinite loops)
		"""
		#not implemented in the abstract base class
		raise NotImplementedError()

	def typecheck(self, vals, valtype):
		if self.valtype == Var.TYPE_STRING:
			#everything is allowed, nothing needs to be modified
			return vals

		elif self.valtype == Var.TYPE_PATH:
			#make sure the path is one of:
			# an absolute POSIX path
			# a smpath
			return [smpathifrel(v, self.conf.directory) for v in vals]

		elif self.valtype == TYPE_INT:
			for v in vals:
				try:
					int(v)
				except:
					raise Exception("Value must be an integer, but is " + v)

		elif type(self.valtype) == list:
			for v in vals:
				if v not in self.valtype:
					raise Exception("Value must be one of " + str(self.valtype)
						+ ", but is " + v)
			return vals

class ValTreeNode_List(ValTreeNode):
	"""
	contains a list of ValTreeNodes
	"""
	def __init__(self, conf, nodes):
		"""
		nodes
			list of ValTreeNodes
		"""
		super().__init__(conf)
		self.nodes = nodes

	def __repr__(self):
		return repr(self.nodes)

	def eval(self, evalconf, valtype, depends):
		result = []
		for node in self.nodes:
			result += node.eval(evalconf, valtype, depends)

		return self.typecheck(result, valtype)

class ValTreeNode_StringLiteral(ValTreeNode):
	"""
	contains one string literal
	"""
	def __init__(self, conf, val):
		"""
		val
			the literal value
		"""
		super().__init__(conf)
		self.val = val

	def __repr__(self):
		return '"' + self.val + '"'

	def eval(self, evalconf, valtype, depends):
		return self.typecheck([val], valtype)

class ValTreeNode_Var(ValTreeNode):
	"""
	evaluates an other variable, by its name
	varname obviously is a ValTreeNode itself
	"""
	def __init__(self, conf, varname):
		"""
		varname
			Variable name (must eval to exactly one string)
		"""
		super().__init__(conf)
		self.varname = varname

	def __repr__(self):
		return '${' + repr(self.varname) + '}'

	def eval(self, evalconf, valtype, depends):
		#first, get the variable name
		varname = self.varname.eval(evalconf, Var.TYPE_STRING, depends)
		if len(varname) != 1:
			#TODO some more sophisticated error reporting
			raise Exception("varname must be exactly one string, but is " + repr(varname))
		varname = varname[0]

		#now, eval that variable
		result = variables[varname[0]].eval(evalconf, depends)

		return self.typecheck(result, valtype)

class ValTreeNode_Fun(ValTreeNode):
	"""
	runs a function, by name and parameters
	"""
	def __init__(self, conf, funname, args):
		"""
		funname
			Function name (must eval to exactly one string)
		args
			Function arguments
			the valtype depends on the function name
		"""
		super().__init__(conf)
		self.funname = funname
		self.args = args

	def __repr__(self):
		return '$(' + repr(self.funname) + ' ' + repr(self.args) + ')'

	def eval(self, evalconf, valtype, depends):
		#first, get the function name
		funname = self.funname.eval(evalconf, Var.TYPE_STRING, depends)
		if len(funname) != 1:
			raise Exception("funnae must be exactly one string, but is " + repr(funname))
		funname = funname[0]

		#TODO modular function concept, with user-definable functions etc etc
		if funname == "count":
			#the 'count' function requires its arguments to be of TYPE_STRING
			args = self.args.eval(evalconf, Var.TYPE_STRING, depends)

			#run the 'count' function magic (its really complicated!)
			result = [str(len(args))]
		elif funname == "path":
			#the 'path' function has the only function to force the evaluation of its args as TYPE_PATH
			args = self.args.eval(evalconf, Var.TYPE_PATH, depends)
			result = args
		else:
			raise Exception("unknown function: " + funname)

		return self.typecheck(result, valtype)

class VarAssignment:
	"""
	represents one assignment of a list of values to a variable, under a certain condition, with a certain mode.

	valtree
		the value tree (type ValTreeNode)
		evals to a list of string values
	condtree
		the condition tree (type CondTreeNode)
		must eval to True for the assignment to take effect
	mode
		if the assignment takes effect, mode selects how it will influence the result list:
		MODE_APPEND (+=) appends valtree.eval() to the result list. existing vals are moved to the end.
		MODE_SET    (=)  replaces the result list with valtree.eval()
		MODE_REOVE  (-=) removes all values in valtree.eval() from the result list.
	src
		a string that describes the source of this assignment, for use in dbg/error messages,
		e.g. '^/smfile, line 80' or 'argv[3]'
	"""

	MODE_APPEND = EnumVal("Assignment mode: Append")
	MODE_SET    = EnumVal("Assignment mode: Set")
	MODE_REMOVE = EnumVal("Assignment mode: Remove")

	def __init__(self, valtree, condtree, mode, src):
		self.valtree = valtree
		self.condtree = condtree
		self.mode = mode
		self.src = src

	def opname(self):
		if self.mode == VarAssignment.MODE_APPEND:
			return '+='
		elif self.mode == VarAssignment.MODE_SET:
			return ':='
		elif self.mode == VarAssignment.MODE_REMOVE:
			return '-='

	def __repr__(self):
		return '[' + repr(self.condtree) + ']' + self.opname() + repr(self.valtree) + " (defined in " + self.src + ")"

class Var:
	"""
	One complete configuration variable, such as 'cflags'.
	Stores lists of VarAssignments for each conf.

	valtype
		the kind of information that is carried in the variable values.
		may be STRING (simple string), PATH (strings will be auto-converted to smpaths),
		or INT (assignment will fail for non-integer strings)
	varquant
		specifies whether the variable stores only a single value (SINGLE),
		or a list of multiple values (MULTI)
	assscope
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
		if self.assscope == Var.SCOPE_CONF:
			self.assignments = {conf_default: defaultassignments}
		elif self.assscope == Var.SCOPE_GLOBAL:
			self.assignments = defaultassignments

		variables[name] = self

	def __repr__(self):
		result = "Name: " + self.name + "\n"
		result += str(self.valtype) + "\n"
		result += str(self.varquant) + "\n"
		result += str(self.assscope) + "\n"
		result += "Assignments:" + "\n"
		if self.assscope == Var.SCOPE_CONF:
			for conf in self.assignments:
				result += repr(conf) + ":\n"
				for ass in self.assignments[conf]:
					result += "  " + repr(ass) + "\n"
		elif self.assscope == Var.SCOPE_GLOBAL:
			for ass in self.assignments:
				result += repr(ass) + "\n"
		return result

	def addassignment(self, assignment, conf):
		"""
		adds the given VarAssignment, scoped for conf
		"""
		if self.assscope == Var.SCOPE_CONF:
			if conf not in self.assignments:
				self.assignments[conf] = [assignment]
			else:
				self.assignments[conf].append(assignment)
		elif self.assscope == Var.SCOPE_GLOBAL:
			self.assignments.append(assignment)

	def eval(self, evalconf, depends = OrderedSet()):
		"""
		returns the string values of the var, for a certain conf.
		evalconf:
			the conf for which we are evaluating
		depends:
			when getting values of a variable, we might need other variables as depends.
			that way, circular dependencies and thus infinite loops may happen.
			we use depends to keep track of these dependencies and detect errors.
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
		if self.varscope == Var.SCOPE_CONF:
			assignments = ((assignment, conf)
				for conf in evalconf.parenthyperres()
				for assignment in self.assignments.get(conf, []))
		elif self.varscope == Var.SCOPE_GLOBAL:
			assignments = ((assignment, conf_default)
				for conf in self.assignments)

		for assignment in assignments:
			#first, check the condition
			if not assignment.condtree.eval(evalconf, depends):
				continue

			vals = assignment.valtree.eval(evalconf, depends, self.valtype)

			#apply assignment strings to result, depending on assignment mode
			if assignment.mode == VarAssignment.MODE_APPEND:
				for v in vals:
					result.append(s)
			elif assignment.mode == VarAssignment.MODE_SET:
				result.clear()
				for v in vals:
					result.append(s)
			elif assignment.mode == VarAssignment.MODE_REMOVE:
				for v in vals:
					result.remove(s)

		if self.varquant == QUANT_SINGLE:
			try:
				return result.newest()
			except:
				raise Exception("Single-quantified variable has no value")
		elif self.varquant == QUANT_MULTI:
			return result

#these global dicts are automatically filled in the constructors of the Confs/Vars.
""" allows quick lookup of Conf objects by their name """
configs = {}

""" the root configuration """
conf_default = Config(name = "default", conftype=Config.TYPE_BASE, parents = [], directory = "^")

""" allows finding Var objects by their name """
variables = {}

#all variables and their default configurations
var_compiler = Var(name = "c", varquant = Var.QUANT_SINGLE, defaultassignments = [
	# c[$srcsuffix == c] = gcc
	VarAssignment(
		valtree = ValTreeNode_StringLiteral(conf_default, "gcc"),
		condtree = CondTreeNode_Leaf_Equals(
			ValTreeNode_Var(conf_default,
				ValTreeNode_StringLiteral(conf_default, "srcsuffix")
			),
			ValTreeNode_StringLiteral(conf_default, "c")
		),
		mode = VarAssignment.MODE_APPEND,
		src = "default configuration"
	),

	# c[$srcsuffix == cpp] = g++
	VarAssignment(
		valtree = ValTreeNode_StringLiteral(conf_default, "g++"),
		condtree = CondTreeNode_Leaf_Equals(
			ValTreeNode_Var(conf_default,
				ValTreeNode_StringLiteral(conf_default, "srcsuffix")
			),
			ValTreeNode_StringLiteral(conf_default, "cpp")
		),
		mode = VarAssignment.MODE_APPEND,
		src = "default configuration"
	)
])
