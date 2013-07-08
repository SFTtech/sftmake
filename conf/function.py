from util.misc import inf

functions = {}

class Function:
	"""
	represents one in-config 'function', which can be used in config files
	"""
	def __init__(self, name, valtype, code, minargc = 0, maxargc = inf):
		"""
		name
			name used to invoke the function in config files
		valtype
			the variable.valtype that the function is expecting
		code
			a python callable, which accepts the conf for which we are
			evaluating as its first argument, followed by any amount
			of string arguments
		minargc
			the minimum number of string arguments that the function requires
		maxargc
			the maximum number of string arguments that the function allows
		"""
		self.name = name
		self.valtype = valtype
		self.code = code
		self.minargc = minargc
		self.maxargc = maxargc
		functions[name] = self

	def call(conf, vallist):
		if len(vallist) < self.minargc:
			raise FunctionTooFewArgumentsException(self.name, len(vallist), self.minargc)
		if len(vallist) > self.maxargc:
			raise FunctionTooMuchArgumentsException(self.name, len(vallist), self.maxargc)

		return self.code(conf, *vallist)
