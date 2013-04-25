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

import parser #python-internal python parser (contains lots of python)
import util

from conf_smfile import smfile

'''
class for working with a smfile
containing configuration written in python
'''
class pysmfile(smfile):

	def __init__(self, filename):
		smfile.__init__(self, filename)

	def run(self):
		smfile_st = parser.suite(self.content)
		smfile_code = parser.compilest(smfile_st, 'smfile-py')

		self.smglobals = globals()
		self.smlocals = {}

		exec(smfile_code, self.smglobals, self.smlocals)

		confvarname = "sftmake"

		if confvarname in self.smlocals.keys():
			self.data = self.smlocals[confvarname]

		else:
			raise Exception("variable "+ confvarname +" not defined in '"+ repr(self) +"'")

	def __repr__(self):
		return "[smfile "+ util.smpath(self.filename) +"]"
