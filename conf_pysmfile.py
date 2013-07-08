#!/usr/bin/python3

# this file is, again, part of [sft]make
#
# licensed GPLv3 or later, no warranty, gschichten.
#
# as the sftmake config language and it's parsing is struggling
# in it's development, this is an attempt to configure sftmake
# via the regular python language
#
# (c) 2013 [sft]technologies, jonas jelten

from logger.levels import *

from conf_smfile import smfile

'''
class for working with a smfile
containing configuration written in python
'''
class pysmfile(smfile):

	#the name of the config variable
	#this has to be set in the smfile
	#TODO!!111
	confvarname = "sftmake"

	def __init__(self, fileobj):
		smfile.__init__(self, fileobj)

	def run(self):
		"""
		parse the content of this smfile
		"""
		try:
			smfile_st = parser.suite(self.get_content())

		except (SyntaxError) as e:
			print(str(dir(e)))

			#flines = self.get_content().split('\n')
			#eline = '"'+ str(flines[e.lineno-1]) +'"'

			msg = "Error parsing python smfile:\n"
			msg += "- Cause: " + e.msg + "\n"
			msg += "- File: " + repr(self) + "\n"
			msg += "- Line: " + str(e.lineno) + ", "
			msg += "Char: " + str(e.offset) + "\n"
			msg += "Expression: \n" + e.text
			msg += ''.join([' ' for i in range(e.offset-1)]) + "^ there..."
			raise Exception(msg)

		#compile the python smfile:
		smfile_code = parser.compilest(smfile_st, "smfile: " + repr(self))

		#preserve global variables, reset local (e.g. smfile_code) variables
		self.smglobals = globals()
		self.smlocals = {}

		#execute the python smfile:
		exec(smfile_code, self.smglobals, self.smlocals)

		if self.confvarname in self.smlocals.keys():
			self.data = self.smlocals[self.confvarname]

		else:
			important("!!! config variable '"+ self.confvarname +"' not defined in '"+ repr(self) +"', ignoring file !!!")


	#this is implemented it pysmfiles superclass
	#def get_associated_smname(self):
		#pass

	def __repr__(self):
		return "pysmfile [" + self.fileobj.filename + "]"

	def __str__(self):
		out = repr(self)
		out += "\nData: " + repr(self.data)
		out += ""
		return out
