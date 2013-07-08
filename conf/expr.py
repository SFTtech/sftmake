import conf.variable as variable
import util

class Expression:
	def __init__(self, conf):
		"""
		conf is the config where the expression was defined
		"""
		self.conf = conf

	def typeconv(self, vals, valtype):
		"""
		converts a list of values to the requested type
		"""
		if valtype == variable.VALTYPE_STRING:
			#everything is allowed, nothing needs to be modified
			return vals

		elif valtype == variable.VALTYPE_PATH:
			#make sure the path is one of:
			# an absolute POSIX path
			# a smpath
			return [smpathifrel(v, self.conf.directory) for v in vals]

		elif valtype == variable.VALTYPE_INT:
			for v in vals:
				try:
					int(v)
				except:
					raise Exception("Value must be an integer, but is " + v)

		elif type(valtype) == list:
			for v in vals:
				if v not in valtype:
					raise Exception("Value must be one of " + str(valtype)
						+ ", but is " + v)
			return vals

	def eval(self, conf, depends, valtype):
		raise NotImplementedError("Abstract base type 'Expression' does not implement 'eval'")

class Literal(Expression):
	"""
	a string literal
	"""
	def __init__(self, conf, value):
		"""
		value:
			String
		"""
		self.value = value
		super().__init__(conf)

	def eval(self, conf, depends, valtype):
		return self.typeconv([self.value], valtype)

class FuncCall(Expression):
	"""
	a call to a config function
	"""
	def __init__(self, conf, funcname, funcargs):
		"""
		funcname:
			Expression
		funcargs:
			ExpressionList
		"""
		self.funcname = funcname
		self.funcargs = funcargs
		super().__init__(conf)

	def eval(self, conf, depends, valtype):
		fname = self.funcname.eval(conf, depends, variable.VALTYPE_STRING)

class ExpressionList(Expression):
	"""
	a list of expressions
	"""
	def __init__(self, conf, expressions):
		"""
		expressions:
			list(Expression)
		"""
		self.expressions = expressions
		super().__init__(conf)

	def eval(self, conf, depends, valtype):
		result = []
		for expr in self.expressions:
			result += expr.eval(conf, depends, valtype)
		return result

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
		varname = self.varname.eval(evalconf, Var.VALTYPE_STRING, depends)
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
		funname = self.funname.eval(evalconf, Var.VALTYPE_STRING, depends)
		if len(funname) != 1:
			raise Exception("funnae must be exactly one string, but is " + repr(funname))
		funname = funname[0]

		#TODO modular function concept, with user-definable functions etc etc
		if funname == "count":
			#the 'count' function requires its arguments to be of VALTYPE_STRING
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
