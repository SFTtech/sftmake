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

import parser #python-internal python parser

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

		exec(smfile_code, globals(), locals())

	def __repr__(self):
		return "[smfile] " + util.smpath(self.filename)
