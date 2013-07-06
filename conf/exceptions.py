class EvaluationException(Exception):
	pass

class VariableUndefinedException(EvaluationException):
	def __init__(self, varname):
		msg = "Variable " + varname + " has no assigned value, and is not of 'list' type"
		self.varname = varname
		EvaluationException.__init__(msg)

class CircularDependencyException(EvaluationException):
	def __init__(self, depends, varname):
		depends = [d.name for d in depends]
		depends.append(varname)
		self.depends = depends
		msg = "Circular dependency: " + ' -> '.join(depends)
		EvaluationException.__init__(msg)

class FunctionEvaluationException(EvaluationException):
	def __init__(self, funcname, msg):
		self.funcname = funcname
		msg = "Could not evaluate function " + funcname + ": " + msg
		EvaluationException.__init__(msg)

class FunctionTooFewArgumentsException(FunctionEvaluationException):
	def __init__(self, funcname, argc, minargc):
		self.argc = argc
		self.minargc = minargc
		msg = "Only " + str(argc) + " of " + str(minargc) + " required arguments given"
		FunctionEvaluationException.__init__(funcname, msg)

class FunctionTooMuchArgumentsException(FunctionEvaluationException):
	def __init__(self, funcname, argc, maxargc):
		self.argc = argc
		self.minargc = minargc
		msg = "More than the maximum " + str(argc) + " arguments given (" + str(maxargc) + ")"
		FunctionEvaluationException.__init__(funcname, msg)
