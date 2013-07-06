from logger.levels import error

def handle_exceptions(function, level = error, exitcode = None, sectionname = None):
	"""
	Calls a function, and handles all unhandled exceptions by passing them to the logger

	function
		The method that will be run
	level
		The log level with which the exceptions are logged
	exitcode
		If specified, exit(exitcode) will be invoked on exception.
		Must be an integer
	sectionname
		If specified, the section name will be printed as the place where the exception
		occured.
	returns
		The exception, if one has occured, or None
	"""
	try:
		function()
		return None
	except Exception as e:
		import traceback

		message = "Unhandled exception"
		if sectionname != None:
			message += " in section '" + sectionname + "'"
		message += "\n"
		message += traceback.format_exc()

		level(message, data = e)

		if exitcode != None:
			exit(exitcode)
		return e
