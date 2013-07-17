import conf.variable as variable
import conf.function as function
import itertools

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
		self.funcnameexpr = funcname
		self.funcargsexpr = funcargs
		super().__init__(conf)

	def eval(self, conf, depends, valtype):
		funcname = self.funcnameexpr.eval(conf, depends, variable.VALTYPE_STRING)
		func = functions[funcname]
		args = self.funcargsexpr.eval(conf, depends, func.valtype)
		ret = func.call(conf, args)
		return self.typeconv(ret, valtype)

class VarSubst(Expression):
	"""
	a substitution with values of an other variable
	"""
	def __init__(self, conf, varname):
		"""
		varname:
			Expression
		"""
		self.varnameexpr = varname
		super().__init__(conf)

	def eval(self, conf, depends, valtype):
		varname = self.varnamexpr.eval(conf, depends, variable.VALTYPE_STRING)
		var = variables[varname]
		ret = var.eval(conf, depends)
		return self.typeconf(ret, valtype)

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

class Concatenation(Expression):
	"""
	a concatenation of multiple expressions
	if some of the members evaluate to nothing, will evaluate to the empty list
	if one of the members evaluate to multiple strings, will evaluate to multiple strings
	if multiple of the members evaluate to multiple strings each, will evaluate to their cross product

	the first member is evaluated with the normal valtype, all others as STRING.
	"""
	def __init__(self, conf, expressions)
		"""
		expressions:
			list(Expression)
		"""
		self.expressions = expressions
		super().__init__(conf)

	def eval(self, conf, depends, valtype):
		crossproduct = itertools.product((
			expr.eval(
				conf,
				depends,
				i == 0 and valtype or variable.VALTYPE_STRING
			)
			for i, expr in enumerate(self.expressions)
		))

		result = ["".join(element) for element in crossproduct]

		return self.typeconv(result, valtype)
